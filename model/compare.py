import pandas as pd
import joblib
import json
import os

from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor


DATA_PATH = "data/processed/supervised_weather.csv"
ARTIFACT_DIR = "model/artifacts"

os.makedirs(ARTIFACT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(DATA_PATH)

    target = "target_temp_t+1"
    features = [c for c in df.columns if c not in ["timestamp", target]]

    X = df[features]
    y = df[target]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, shuffle=False
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, shuffle=False
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def evaluate(model, X, y):
    preds = model.predict(X)
    return {
        "mae": mean_absolute_error(y, preds),
        "rmse": root_mean_squared_error(y, preds)
    }


def main():
    X_train, X_val, X_test, y_train, y_val, y_test = load_data()

    experiments = []

    models = {
        "LinearRegression": (
            Pipeline([
                ("scaler", StandardScaler()),
                ("model", LinearRegression())
            ]),
            {}
        ),

        "Ridge": (
            Pipeline([
                ("scaler", StandardScaler()),
                ("model", Ridge())
            ]),
            {"model__alpha": [0.01, 0.1, 1.0, 10.0]}
        ),

        "Lasso": (
            Pipeline([
                ("scaler", StandardScaler()),
                ("model", Lasso(max_iter=5000))
            ]),
            {"model__alpha": [0.001, 0.01, 0.1]}
        ),

        "RandomForest": (
            RandomForestRegressor(random_state=42, n_jobs=-1),
            {
                "n_estimators": [100, 200],
                "max_depth": [8, 12, None],
                "min_samples_leaf": [3, 5]
            }
        ),

        "GradientBoosting": (
            GradientBoostingRegressor(random_state=42),
            {
                "n_estimators": [100, 200],
                "learning_rate": [0.05, 0.1],
                "max_depth": [2, 3]
            }
        )
    }

    for name, (model, grid) in models.items():
        print(f"\n🔍 Tuning {name}")

        if grid:
            search = GridSearchCV(
                model,
                grid,
                scoring="neg_mean_absolute_error",
                cv=3
            )
            search.fit(X_train, y_train)
            best_model = search.best_estimator_
            best_params = search.best_params_
        else:
            model.fit(X_train, y_train)
            best_model = model
            best_params = {}

        val_metrics = evaluate(best_model, X_val, y_val)
        test_metrics = evaluate(best_model, X_test, y_test)

        experiments.append({
            "model": name,
            "val_mae": val_metrics["mae"],
            "val_rmse": val_metrics["rmse"],
            "test_mae": test_metrics["mae"],
            "test_rmse": test_metrics["rmse"],
            "params": best_params
        })

        joblib.dump(best_model, f"{ARTIFACT_DIR}/{name}_best.pkl")

    results = pd.DataFrame(experiments).sort_values("val_mae")
    print("\n📊 Tuned Model Comparison")
    print(results)

    best = results.iloc[0]
    with open(f"{ARTIFACT_DIR}/best_model.json", "w") as f:
        json.dump(best.to_dict(), f, indent=2)

    print(f"\n🏆 Selected Model: {best['model']}")


if __name__ == "__main__":
    main()
