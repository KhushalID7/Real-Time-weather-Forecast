import os
import sys
import subprocess


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PYTHON = sys.executable


def run_step(name, command):
    print(f"\n🚀 {name}")
    result = subprocess.run(
        command,
        shell=True,
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        raise RuntimeError(f"❌ Step failed: {name}")


def retrain():
    run_step(
        "Preparing training data",
        f'"{PYTHON}" -m ingestion.prepare_training_data'
    )

    run_step(
        "Training & selecting best model",
        f'"{PYTHON}" -m model.compare'
    )

    print("\n✅ Retraining completed successfully")


if __name__ == "__main__":
    retrain()
