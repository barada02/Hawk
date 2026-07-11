# ---- Hawkeye backend image (Cloud Run ready) ----
FROM python:3.13-slim

# - PYTHONUNBUFFERED: stream logs straight to Cloud Run (no buffering)
# - PYTHONDONTWRITEBYTECODE: no .pyc clutter
# - PORT: Cloud Run overrides this at runtime; 8080 is its default contract
# - DEBUG: disable reload / FastAPI debug in the deployed image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DEBUG=false

WORKDIR /app

# Install deps first so this layer caches unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

EXPOSE 8080

# Bind to 0.0.0.0 and the Cloud Run-provided $PORT (shell form expands it).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
