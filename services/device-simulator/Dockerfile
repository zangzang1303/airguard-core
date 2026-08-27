FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY device_simulator.py .
COPY __init__.py .

CMD ["python", "device_simulator.py"]
