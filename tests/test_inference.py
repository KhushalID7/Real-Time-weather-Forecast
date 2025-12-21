import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from model.inference import ModelInferenceEngine

# Load inference engine
engine = ModelInferenceEngine()

# Example: load last few rows as inference input
df = pd.read_csv("data/processed/supervised_weather.csv")

target = "target_temp_t+1"
features = [c for c in df.columns if c not in ["timestamp", target]]

X_sample = df[features].tail(5)

preds = engine.predict(X_sample)

param_name = target.replace("target_", "").replace("_t+1", "")
timestamps = df["timestamp"].tail(len(X_sample)).values
preds_arr = np.asarray(preds).reshape(-1)

results = [{"timestamp": ts, param_name: float(p)} for ts, p in zip(timestamps, preds_arr)]
print("Predictions every hour🕛")
for result in results:
    print(result)
