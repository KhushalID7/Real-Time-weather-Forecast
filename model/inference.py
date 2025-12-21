import json
import joblib
import pandas as pd
import os


ARTIFACT_DIR = "model/artifacts"
BEST_MODEL_PATH = os.path.join(ARTIFACT_DIR, "best_model.json")


class ModelInferenceEngine:
    def __init__(self):
        self.model = None
        self.model_name = None
        self.load_best_model()

    def load_best_model(self):
        """Load the best model based on metadata"""
        with open(BEST_MODEL_PATH, "r") as f:
            metadata = json.load(f)

        self.model_name = metadata["model"]
        model_path = os.path.join(
            ARTIFACT_DIR,
            f"{self.model_name}_best.pkl"
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        self.model = joblib.load(model_path)

        print(f"✅ Loaded best model: {self.model_name}")

    def predict(self, X: pd.DataFrame):
        """Run inference"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        return self.model.predict(X)