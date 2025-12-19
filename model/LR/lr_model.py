import pandas as pd
import joblib
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
# from sklearn.metrics import root_mean_squared_error  # optional: if sklearn >= 1.4


def time_split(df,train_ratio=0.7,val_ratio=0.15):
    n =len(df)
    train_end = int(n*train_ratio)
    val_end = int(n*(train_ratio + val_ratio))
    return df[:train_end], df[train_end:val_end], df[val_end:]


def train_LR(data_path):
    df = pd.read_csv(data_path)

    target_col = "target_temp_t+1"
    feature_cols = [c for c in df.columns if c not in ["timestamp", target_col]]

    train, val, test = time_split(df)

    X_train, y_train = train[feature_cols], train[target_col]
    X_val, y_val = val[feature_cols], val[target_col]
    X_test, y_test = test[feature_cols], test[target_col]

    # ----------------------------
    # Model
    # ----------------------------
    model = LinearRegression()
    model.fit(X_train, y_train)

    # ----------------------------
    # Evaluation
    # ----------------------------
    val_pred = model.predict(X_val)
    test_pred = model.predict(X_test)

    val_mae = mean_absolute_error(y_val, val_pred)
    val_rmse = mean_squared_error(y_val, val_pred, squared=False)  # or: root_mean_squared_error(y_val, val_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    test_rmse = mean_squared_error(y_test, test_pred, squared=False)  # or: root_mean_squared_error(y_test, test_pred)

    print("📊 Linear Regression Results")
    print(f"Validation MAE : {val_mae:.4f}")
    print(f"Validation RMSE: {val_rmse:.4f}")
    print(f"Test MAE       : {test_mae:.4f}")
    print(f"Test RMSE      : {test_rmse:.4f}")

    # ----------------------------
    # Save model
    # ----------------------------
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"   # -> project_root/model/artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "lr_model_v1.pkl"
    joblib.dump(model, model_path)
    print(f"✅ Model saved at {model_path}")

    return model


if __name__ == "__main__":
    train_LR("data/processed/supervised_weather.csv")