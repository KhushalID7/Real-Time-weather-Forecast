import json
import joblib
import pandas as pd
import os


ARTIFACT_DIR = "model/artifacts"
BEST_MODEL_PATH = os.path.join(ARTIFACT_DIR, "best_model.pkl")
BEST_META_PATH = os.path.join(ARTIFACT_DIR, "best_model_meta.json")


class ModelInferenceEngine:
    def __init__(self):
        self.model = None
        self.model_name = None
        self.load_best_model()

    def load_best_model(self):
        """Load the best model based on metadata"""
        with open(BEST_META_PATH, "r") as f:
            metadata = json.load(f)

        # Backward-compatible name field
        self.model_name = metadata.get("model_name") or metadata.get("model")

        if not os.path.exists(BEST_MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {BEST_MODEL_PATH}")

        self.model = joblib.load(BEST_MODEL_PATH)
        print(f"✅ Loaded best model: {self.model_name}")

    def predict(self, X: pd.DataFrame):
        """Run inference"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        return self.model.predict(X)