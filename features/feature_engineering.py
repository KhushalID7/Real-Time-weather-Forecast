import pandas as pd

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
    df = df.dropna().reset_index(drop=True)

    return df

