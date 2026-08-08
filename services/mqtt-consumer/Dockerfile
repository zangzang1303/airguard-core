FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mqtt_consumer ./mqtt_consumer

CMD ["python", "-m", "mqtt_consumer.main"]
