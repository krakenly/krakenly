# Configuration

This document describes all configuration options for Krakenly.

## Environment Variables

Environment variables can be set in `docker-compose.yml` under the `api` service:

```yaml
services:
  api:
    environment:
      - MODEL_NAME=qwen2.5:3b
      - MAX_TOKENS=512
      - TEMPERATURE=0.7
```

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `qwen2.5:3b` | Ollama model to use for text generation |
| `MAX_TOKENS` | `512` | Maximum tokens for AI responses |
| `TEMPERATURE` | `0.7` | Model temperature (0.0-1.0, higher = more creative) |

### Embedding Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Model for text embeddings (high-quality retrieval) |

### Performance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_WORKERS` | `2` | Gunicorn worker processes |
| `API_THREADS` | `2` | Threads per worker |
| `OLLAMA_NUM_THREADS` | `4` | Ollama CPU threads for inference |

---

## Available Models

### Ollama Language Models

These models can be used for text generation (set via `MODEL_NAME`):

| Model | Size | Parameters | Notes |
|-------|------|------------|-------|
| `qwen2.5:3b` | 1.9GB | 3B | **Default** - Excellent quality, good speed |
| `qwen2.5:0.5b` | 400MB | 0.5B | Ultra-fast, lower quality |
| `qwen2.5:7b` | 4.4GB | 7B | Higher quality, slower |
| `phi3:mini` | 2.3GB | 3.8B | Good balance of speed/quality |
| `llama3.2:1b` | 1.3GB | 1B | Fast, good quality |
| `llama3.2:3b` | 2.0GB | 3B | Similar to qwen2.5:3b |
| `gemma2:2b` | 1.6GB | 2B | Google's efficient model |
| `mistral:7b` | 4.1GB | 7B | Strong reasoning |

### Embedding Models

These models convert text to vectors for semantic search (set via `EMBEDDING_MODEL`):

| Model | Description |
|-------|-------------|
| `BAAI/bge-small-en-v1.5` | **Default** - Optimized for retrieval tasks |
| `sentence-transformers/all-MiniLM-L6-v2` | Faster, general purpose |
| `BAAI/bge-base-en-v1.5` | Larger, higher quality |

---

## Changing Models

### Change Language Model

1. Edit `docker-compose.yml`:
   ```yaml
   environment:
     - MODEL_NAME=phi3:mini
   ```

2. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. The new model will be downloaded automatically on first request.

### Pull Model Manually

You can pre-download a model via API:

```bash
curl -X POST http://localhost:5000/models/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "phi3:mini"}'
```

Or via Ollama directly:

```bash
docker-compose exec ollama ollama pull phi3:mini
```

### Change Embedding Model

1. Edit `docker-compose.yml`:
   ```yaml
   environment:
     - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

2. Rebuild the API service:
   ```bash
   docker-compose down
   docker-compose up -d --build api
   ```

> **Warning:** Changing the embedding model requires re-indexing all documents, as vectors are not compatible between models.

---

## Performance Tuning

### Low Memory Systems (8GB RAM)

For systems with limited memory:

```yaml
environment:
  - MODEL_NAME=qwen2.5:0.5b  # Smaller model
  - MAX_TOKENS=256            # Shorter responses
  - API_WORKERS=1             # Single worker
  - OLLAMA_NUM_THREADS=2      # Fewer threads
```

### High Performance Systems (16GB+ RAM)

For systems with more resources:

```yaml
environment:
  - MODEL_NAME=qwen2.5:7b     # Larger model
  - MAX_TOKENS=1024           # Longer responses
  - API_WORKERS=4             # More workers
  - OLLAMA_NUM_THREADS=8      # More threads
```

### GPU Acceleration

If you have an NVIDIA GPU, add to `docker-compose.yml`:

```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## Docker Volume Configuration

Data is stored in Docker volumes defined in `docker-compose.yml`:

```yaml
volumes:
  ollama_data:    # Models (~1.9GB+ per model)
  chroma_data:    # Vector database
```

### Custom Volume Locations

To use host directories instead of Docker volumes:

```yaml
services:
  ollama:
    volumes:
      - /path/to/ollama:/root/.ollama
  
  chromadb:
    volumes:
      - /path/to/chroma:/chroma/chroma
```

---

## Network Configuration

### Port Mapping

Default port configuration:

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Web Manager | 80 | 8080 |
| API | 5000 | 5000 |
| Ollama | 11434 | 11434 |
| ChromaDB | 8000 | 8000 |

To change external ports, modify `docker-compose.yml`:

```yaml
services:
  web-manager:
    ports:
      - "3000:80"  # Access at localhost:3000
```

### Binding to Specific Interfaces

By default, services bind to all interfaces (`0.0.0.0`). To bind to localhost only:

```yaml
services:
  api:
    ports:
      - "127.0.0.1:5000:5000"
```

---

## Logging Configuration

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ollama
```

### Log Levels

Set log verbosity in the API service:

```yaml
environment:
  - LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## Example Configurations

### Minimal Configuration (Low Resources)

```yaml
services:
  api:
    environment:
      - MODEL_NAME=qwen2.5:0.5b
      - MAX_TOKENS=128
      - API_WORKERS=1
      - OLLAMA_NUM_THREADS=2
```

### Balanced Configuration (Default)

```yaml
services:
  api:
    environment:
      - MODEL_NAME=qwen2.5:3b
      - MAX_TOKENS=512
      - TEMPERATURE=0.7
      - EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
      - API_WORKERS=2
      - API_THREADS=2
      - OLLAMA_NUM_THREADS=4
```

### Maximum Quality Configuration

```yaml
services:
  api:
    environment:
      - MODEL_NAME=qwen2.5:7b
      - MAX_TOKENS=2048
      - TEMPERATURE=0.5
      - EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
      - API_WORKERS=4
      - OLLAMA_NUM_THREADS=8
```
