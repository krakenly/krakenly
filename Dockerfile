# Krakenly - Unified Docker Image (API + Web UI)
# https://github.com/krakenly/krakenly
#
# This image bundles the REST API and web interface.
# Requires external Ollama and ChromaDB services.
#
# Usage:
#   docker run -p 8080:80 -p 5000:5000 \
#     -e OLLAMA_HOST=http://host.docker.internal:11434 \
#     -e CHROMA_HOST=http://host.docker.internal:8000 \
#     krakenly/krakenly

FROM python:3.10-slim AS builder

WORKDIR /app

# Install Python dependencies in builder stage
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.10-slim

# Image metadata for DockerHub
LABEL org.opencontainers.image.title="Krakenly"
LABEL org.opencontainers.image.description="AI-powered document search and indexing with RAG capabilities"
LABEL org.opencontainers.image.url="https://github.com/krakenly/krakenly"
LABEL org.opencontainers.image.source="https://github.com/krakenly/krakenly"
LABEL org.opencontainers.image.vendor="Krakenly"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintainer="Krakenly <hello@krakenly.io>"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nginx \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy API application
COPY services/api/config.py .
COPY services/api/services/ services/
COPY services/api/utils/ utils/
COPY services/api/app.py .

# Copy web UI static files
COPY services/web-manager/static/ /usr/share/nginx/html/

# Copy nginx configuration
COPY services/web-manager/nginx.conf /etc/nginx/conf.d/default.conf

# Copy supervisor config
COPY supervisor.conf /etc/supervisor/conf.d/krakenly.conf

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/run /data \
    && chown -R www-data:www-data /usr/share/nginx/html \
    && chown -R www-data:www-data /data

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    OLLAMA_HOST=http://localhost:11434 \
    CHROMA_HOST=http://localhost:8000 \
    MODEL_NAME=qwen2.5:3b \
    EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 \
    API_WORKERS=2 \
    API_THREADS=2 \
    API_TIMEOUT=300 \
    INDEX_METADATA_FILE=/data/index_metadata.json

# Volume for persistent data
VOLUME ["/data"]

# Expose ports: 80 (Web UI), 5000 (API)
EXPOSE 80 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health && curl -f http://localhost:80/health || exit 1

# Start supervisor (manages both nginx and gunicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
