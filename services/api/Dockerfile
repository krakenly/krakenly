# API Service - Thin REST API layer with embeddings
FROM python:3.10-slim

WORKDIR /app

# Install curl for health checks
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Copy application code
COPY config.py .
COPY services/ services/
COPY utils/ utils/
COPY app.py .

# Ensure Python output is not buffered (for logging during startup)
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Workers and threads configurable via environment variables
# API_WORKERS: number of gunicorn worker processes (default: 2)
# API_THREADS: threads per worker (default: 2)
# API_TIMEOUT: request timeout in seconds (default: 300)
# Using --preload to load embedding model once and share across workers
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 --workers ${API_WORKERS:-2} --threads ${API_THREADS:-2} --timeout ${API_TIMEOUT:-300} --preload app:app"]
