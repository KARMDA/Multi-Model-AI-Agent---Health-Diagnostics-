FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline ./pipeline
COPY model2_runner.py .

# 👇 THIS IS THE KEY FIX
ENTRYPOINT ["python", "model2_runner.py"]
