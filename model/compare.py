import os, sys
import json
import joblib
import pandas as pd

from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
# optionally try xgboost if installed



# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DATA_PATH = "data/processed/supervised_weather.csv"
ARTIFACT_DIR = "model/artifacts"

BEST_MODEL_PATH = os.path.join(ARTIFACT_DIR, "best_model.pkl")
BEST_META_PATH = os.path.join(ARTIFACT_DIR, "best_model_meta.json")


def train_val_test_split_time(df, train_ratio=0.7, val_ratio=0.15):
    """
    Time-aware split:
    Train = first 70%
    Val   = next 15%
    Test  = last 15%
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    df_train = df.iloc[:train_end]
    df_val = df.iloc[train_end:val_end]
    df_test = df.iloc[val_end:]

    return df_train, df_val, df_test


def evaluate(model, X, y):
    pred = model.predict(X)
    mae = mean_absolute_error(y, pred)
    rmse = root_mean_squared_error(y, pred)
    return mae, rmse


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"❌ Missing dataset: {DATA_PATH}")

    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    target_col = "target_temp_t+1"
    drop_cols = ["timestamp", target_col]

    X = df.drop(columns=drop_cols)
    y = df[target_col]

    # Time split
    df_train, df_val, df_test = train_val_test_split_time(df)

    X_train = df_train.drop(columns=drop_cols)
    y_train = df_train[target_col]

    X_val = df_val.drop(columns=drop_cols)
    y_val = df_val[target_col]

    X_test = df_test.drop(columns=drop_cols)
    y_test = df_test[target_col]

    # TimeSeries CV
    tscv = TimeSeriesSplit(n_splits=5)

    # -------------------------------------------------
    # Models + grids
    # -------------------------------------------------
    models = [
        ("LinearRegression", LinearRegression(), {}),
        ("Ridge", Ridge(), {"model__alpha": [0.01, 0.1, 1.0, 10.0, 50.0]}),
        ("RandomForest", RandomForestRegressor(random_state=42), {
            "model__n_estimators": [100, 200],
            "model__max_depth": [10, 20],
            "model__min_samples_leaf": [3, 5],
        }),
        ("GradientBoosting", GradientBoostingRegressor(random_state=42), {
            "model__n_estimators": [100, 200],
            "model__learning_rate": [0.05, 0.1],
            "model__max_depth": [2, 3],
        }),
        ("HistGradientBoosting", HistGradientBoostingRegressor(random_state=42), {
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__max_depth": [3, 5, None],
            "model__max_iter": [200, 400],
        })
    ]
    

    results = []
    best_overall = None

    for name, model, grid in models:
        print(f"\n🔍 GridSearch: {name}")

        # Scaling helps linear models, harmless for trees
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("model", model)
        ])

        # Use environment variable for n_jobs, default to 1 for memory safety on small droplets
        n_jobs = int(os.environ.get("ML_N_JOBS", 1))

        gs = GridSearchCV(
            estimator=pipe,
            param_grid=grid,
            scoring="neg_root_mean_squared_error",
            cv=tscv,
            n_jobs=n_jobs,
            verbose=1  # increased verbose level slightly to show progress
        )

        gs.fit(X_train, y_train)

        best_model = gs.best_estimator_
        best_params = gs.best_params_

        val_mae, val_rmse = evaluate(best_model, X_val, y_val)
        test_mae, test_rmse = evaluate(best_model, X_test, y_test)

        results.append({
            "model": name,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "test_mae": test_mae,
            "test_rmse": test_rmse,
            "params": best_params
        })

        print(f"✅ Best params: {best_params}")
        print(f"📌 Val  MAE={val_mae:.4f} | RMSE={val_rmse:.4f}")
        print(f"📌 Test MAE={test_mae:.4f} | RMSE={test_rmse:.4f}")

        # Pick best by validation RMSE
        if best_overall is None or val_rmse < best_overall["val_rmse"]:
            best_overall = {
                "model_name": name,
                "model_obj": best_model,
                "val_rmse": val_rmse,
                "params": best_params
            }

    # -------------------------------------------------
    # Save best model
    # -------------------------------------------------
    joblib.dump(best_overall["model_obj"], BEST_MODEL_PATH)

    meta = {
        "model_name": best_overall["model_name"],
        "val_rmse": best_overall["val_rmse"],
        "params": best_overall["params"],
        "feature_columns": list(X.columns)
    }

    with open(BEST_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    df_results = pd.DataFrame(results).sort_values("val_rmse")
    print("\n📊 Tuned Model Comparison (sorted by val_rmse)")
    print(df_results)

    print("\n🏆 Best Model:", best_overall["model_name"])
    print("💾 Saved:", BEST_MODEL_PATH)
    print("📝 Meta:", BEST_META_PATH)


if __name__ == "__main__":
    main()
