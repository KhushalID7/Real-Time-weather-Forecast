# Use an official Python 3.10 slim image
FROM python:3.10-slim

# Set workspace
WORKDIR /app

# Install system dependencies (for some python packages if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the model artifacts directory exists
RUN mkdir -p model/artifacts

# Default command (can be overridden in docker-compose)
CMD ["python", "streaming/inference_consumer.py"]
