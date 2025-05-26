FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

#CMD ["python", "-m", "streamer.cli", "-c", "config.yaml"]
CMD ["python", "main.py", "--config", "config.yaml"]