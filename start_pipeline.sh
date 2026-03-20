#!/bin/bash
set -e
# 🌦️ Real-Time Weather Forecast Launcher (Ubuntu/Linux)

echo "======================================================="
echo "    Starting Real-Time Weather Forecast Pipeline"
echo "======================================================="

# 1. Start Kafka and Zookeeper
echo "[1/5] Starting Kafka and Zookeeper via Docker..."
cd docker && docker compose up -d
cd ..

echo "Waiting for Kafka to be ready (10s)..."
sleep 10

# 2. Prepare Data
echo "[2/5] Preparing training data..."
python3 ingestion/prepare_training_data.py

# 3. Train Model
echo "[3/5] Training and selecting the best ML model..."
python3 model/compare.py

# 4. Start Background Services
echo "[4/5] Starting backend background services..."
# Using '&' to run in background. logs will be sent to .log files
nohup python3 streaming/weather_producer.py > producer.log 2>&1 &
echo "✔ Weather Producer started (PID: $!)"

nohup python3 streaming/inference_consumer.py > consumer.log 2>&1 &
echo "✔ Inference Consumer started (PID: $!)"

nohup python3 orchestration/scheduler.py > scheduler.log 2>&1 &
echo "✔ Scheduler started (PID: $!)"

# 5. Start Streamlit
echo "[5/5] Starting Streamlit Dashboard..."
nohup streamlit run app/Home.py --server.address 0.0.0.0 > streamlit.log 2>&1 &
echo "✔ Streamlit Dashboard started (PID: $!)"

echo "======================================================="
echo "All services are running in the background!"
echo "Dashboard: http://localhost:8501"
echo "Check *.log files for output (e.g., 'tail -f streamlit.log')"
echo "======================================================="
