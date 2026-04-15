import joblib
import sklearn
import os
import sys

MODEL_PATH = "model/artifacts/best_model.pkl"

if os.path.exists(MODEL_PATH):
    print(f"Loading {MODEL_PATH}...")
    try:
        model = joblib.load(MODEL_PATH)
        print("SUCCESS: Load successful locally!")
        
        # Try to find version if it's a scikit-learn object
        if hasattr(model, '_sklearn_version'):
            print(f"Model trained with sklearn version: {model._sklearn_version}")
        elif hasattr(model, 'named_steps'): # if it's a pipeline
            # check version of the last step
            last_step = list(model.named_steps.values())[-1]
            if hasattr(last_step, '_sklearn_version'):
                print(f"Model (pipeline) trained with sklearn version: {last_step._sklearn_version}")
        
    except Exception as e:
        print(f"ERROR: Load failed locally: {e}")
else:
    print(f"File not found: {MODEL_PATH}")

print(f"Current local sklearn version: {sklearn.__version__}")
print(f"Current local joblib version: {joblib.__version__}")
