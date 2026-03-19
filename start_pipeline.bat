@echo off
title 🌦️ Real-Time Weather Forecast Launcher
echo =======================================================
echo     Starting Real-Time Weather Forecast Pipeline
echo =======================================================
echo.

echo [1/5] Starting Kafka and Zookeeper via Docker...
cd docker
docker compose up -d
cd ..
echo Waiting for Kafka to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [2/5] Preparing training data...
python ingestion/prepare_training_data.py

echo.
echo [3/5] Training and selecting the best ML model...
python model/compare.py

echo.
echo [4/5] Starting backend background services...
:: We use 'start' to open a new command prompt for each long-running service
start "Weather Producer" cmd /k "python streaming/weather_producer.py"
start "Inference Consumer" cmd /k "python streaming/inference_consumer.py"
start "Scheduler" cmd /k "python orchestration/scheduler.py"

echo.
echo [5/5] Starting Streamlit Dashboard...
start "Streamlit Dashboard" cmd /k "streamlit run app/Home.py"

echo.
echo =======================================================
echo All services have been started!
echo The Streamlit dashboard should open in your browser shortly at http://localhost:8501.
echo You can monitor the backend services in the newly opened command prompt windows.
echo =======================================================
pause
