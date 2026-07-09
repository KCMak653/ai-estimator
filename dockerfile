# Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
# node runs the bundled estimate-PDF renderer (pdf_service/render_estimate.cjs);
# the bundle is checked in, so the runtime is all we need — no npm install.
RUN apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
# Railway provides $PORT; default to 8000 locally
CMD sh -c "uvicorn chatbot_app:app --host 0.0.0.0 --port ${PORT:-8000}"
