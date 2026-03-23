#!/bin/bash
set -e

echo "======================================================="
echo "    Starting Real-Time Weather Forecast Pipeline"
echo "======================================================="

# 0) Base deps (safe to re-run)
echo "[0/7] Installing base packages..."
sudo apt-get update -y
sudo apt-get install -y git git-lfs curl ca-certificates python3 python3-venv python3-pip docker.io

echo "[0/7] Enabling Docker..."
sudo systemctl enable docker
sudo systemctl start docker
git lfs install

# 1) Pull LFS artifacts
echo "[1/7] Pulling Git LFS artifacts..."
git lfs pull

# 2) Python venv + deps
echo "[2/7] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3) Start Kafka/Zookeeper (Docker)
echo "[3/7] Starting Kafka and Zookeeper via Docker..."
cd docker && sudo docker compose up -d
cd ..
echo "Waiting for Kafka to be ready (45s)..."
sleep 45

# 4) Prepare data + train model
echo "[4/7] Preparing training data..."
python ingestion/prepare_training_data.py

echo "[5/7] Training and selecting the best ML model..."
python model/compare.py

# 5) Start services (background)
echo "[6/7] Starting backend background services..."
nohup python -u streaming/weather_producer.py > producer.log 2>&1 &
echo "✔ Weather Producer started (PID: $!)"

nohup python -u streaming/inference_consumer.py > consumer.log 2>&1 &
echo "✔ Inference Consumer started (PID: $!)"

nohup python -u orchestration/scheduler.py > scheduler.log 2>&1 &
echo "✔ Scheduler started (PID: $!)"

# 6) Start Streamlit (background)
echo "[7/7] Starting Streamlit Dashboard..."
nohup streamlit run app/Home.py --server.address 0.0.0.0 > streamlit.log 2>&1 &
echo "✔ Streamlit Dashboard started (PID: $!)"

echo "======================================================="
echo "All services are running in the background!"
echo "Dashboard: http://localhost:8501"
echo "Logs: producer.log consumer.log scheduler.log streamlit.log"
echo "======================================================="