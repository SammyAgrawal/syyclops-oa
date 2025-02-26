FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY router.py .
COPY devices.py .

RUN mkdir -p /app/logs

CMD ["python", "router.py"]