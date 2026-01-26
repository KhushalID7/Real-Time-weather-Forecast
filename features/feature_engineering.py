import pandas as pd
import numpy as np

def create_supervised_dataset(hourly_data, n_lags = 6):

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly_data["time"]),
        "temperature": hourly_data["temperature_2m"],
        "humidity": hourly_data["relative_humidity_2m"],
        "wind_speed": hourly_data["wind_speed_10m"],
        "pressure": hourly_data["surface_pressure"]
    })


    df = df.sort_values("timestamp").reset_index(drop=True)

    for lag in range(1, n_lags + 1):
        df[f"temp_t-{lag}"] = df["temperature"].shift(lag)
        df[f"humidity_t-{lag}"] = df["humidity"].shift(lag)
        df[f"wind_speed_t-{lag}"] = df["wind_speed"].shift(lag)
        df[f"pressure_t-{lag}"] = df["pressure"].shift(lag)

    
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    df["target_temp_t+1"] = df["temperature"].shift(-1)
    
    # ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # --- time-based cyclic features ---
    df["month"] = df["timestamp"].dt.month
    df["day_of_year"] = df["timestamp"].dt.dayofyear

    hour = df["timestamp"].dt.hour
    df["sin_hour"] = np.sin(2 * np.pi * hour / 24)
    df["cos_hour"] = np.cos(2 * np.pi * hour / 24)

    doy = df["timestamp"].dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)

    # --- slope / trend features ---
    # temp_t-1, temp_t-2, ... assumed present from existing code
    df["temp_diff_1"] = df["temp_t-1"] - df["temp_t-2"]
    df["temp_diff_2"] = df["temp_t-2"] - df["temp_t-3"]

    # rolling means over recent lags
    df["temp_rm_3"] = df[["temp_t-1", "temp_t-2", "temp_t-3"]].mean(axis=1)
    df["temp_rm_6"] = df[["temp_t-1", "temp_t-2", "temp_t-3", "temp_t-4", "temp_t-5", "temp_t-6"]].mean(axis=1)

    # drop any rows with NA after feature creation
    df = df.dropna().reset_index(drop=True)

    df = df.drop(columns=[
    "temperature",
    "humidity",
    "wind_speed",
    "pressure"
    ])

    return df

