FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install cognee with Ollama extras
RUN pip install --no-cache-dir \
        "cognee[ollama]" \
        httpx

# Copy application
COPY app/ /app/

# Data directory for optional user files
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]
