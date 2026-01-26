cd docker

docker compose up -d
docker exec -it docker-kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 --topic weather_raw




python streaming/inference_consumer.py



python streaming/weather_producer.py



python orchestration/scheduler.py


streamlit run app/Home.py
