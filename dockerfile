# Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
# Railway provides $PORT; default to 8000 locally
CMD sh -c "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"
