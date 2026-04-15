import json
import joblib
import sklearn
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

        print(f"DEBUG: Attempting to load model from: {os.path.abspath(BEST_MODEL_PATH)}")
        print(f"DEBUG: File size: {os.path.getsize(BEST_MODEL_PATH)} bytes")
        print(f"DEBUG: Local sklearn version: {sklearn.__version__}")
        print(f"DEBUG: Local joblib version: {joblib.__version__}")

        try:
            self.model = joblib.load(BEST_MODEL_PATH)
            print(f"✅ Loaded best model: {self.model_name}")
        except Exception as e:
            print(f"❌ CRITICAL LOAD ERROR: {e}")
            print(f"System Info: Python={os.sys.version}")
            raise e

    def predict(self, X: pd.DataFrame):
        """Run inference"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        return self.model.predict(X)