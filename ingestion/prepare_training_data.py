import os
import requests
from features.feature_engineering import create_supervised_dataset

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 23.2167,
    "longitude": 72.6833,
    "start_date": "2024-09-01",
    "end_date": "2024-12-01",
    "hourly": ",".join([
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "surface_pressure"
    ]),
    "timezone": "auto"
}

response = requests.get(ARCHIVE_URL, params=params)
response.raise_for_status()

hourly_data = response.json()["hourly"]

df_supervised = create_supervised_dataset(hourly_data, n_lags=6)

output_dir = "data/processed"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "supervised_weather.csv")
df_supervised.to_csv(output_path, index=False)

print("✅ Supervised dataset created")
print("Path:", output_path)
print("Dataset shape:", df_supervised.shape)
print("Total NaNs:", df_supervised.isnull().sum().sum())
print("Feature columns:", len(df_supervised.columns) - 2)
print(df_supervised.head())
