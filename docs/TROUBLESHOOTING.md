# Troubleshooting

This guide covers common issues and their solutions.

## Services Not Starting

Check container status and logs:

```bash
docker-compose ps
docker-compose logs
```

**Common causes:**
- Docker not running: `sudo systemctl start docker`
- Port conflicts: Check if ports 5000, 8000, 8080, or 11434 are in use
- Insufficient memory: Ensure at least 8GB RAM available

## AI Model Slow on First Request

The first request after starting services loads the model into memory (10-30 seconds). Subsequent requests are fast.

**To pre-warm the model:**

```bash
curl http://localhost:5000/health
```

This triggers model loading so your first real query is fast.

## Out of Memory

The `qwen2.5:3b` model needs ~4GB RAM during inference.

**Check Docker's memory allocation:**

```bash
docker info | grep Memory
```

**Solutions:**
- Close other applications to free memory
- Use a smaller model: Set `MODEL_NAME=qwen2.5:0.5b` in `docker-compose.yml`
- Increase Docker's memory limit (Docker Desktop settings)

## Search Returns No Results

**Check if data is indexed:**

```bash
curl http://localhost:5000/stats
```

If `total_documents` is 0, you need to index data first.

**Index test data:**

```bash
curl -X POST http://localhost:5000/index \
  -H "Content-Type: application/json" \
  -d '{"text": "Test content", "metadata": {"source": "test.txt"}}'
```

## Container Keeps Restarting

Check container logs for errors:

```bash
docker-compose logs api
docker-compose logs ollama
docker-compose logs chromadb
```

**Common fixes:**
- Rebuild images: `docker-compose up -d --build`
- Clean restart: `docker-compose down && docker-compose up -d`
- Full cleanup: `./scripts/cleanup.sh && ./scripts/start.sh`

## Ollama Model Download Fails

If the model download is interrupted:

```bash
# Remove partial download
docker-compose exec ollama ollama rm qwen2.5:3b

# Re-download
docker-compose exec ollama ollama pull qwen2.5:3b
```

## Port Already in Use

If you see "port is already allocated" errors:

```bash
# Find what's using the port (e.g., 5000)
lsof -i :5000

# Kill the process or change the port in docker-compose.yml
```

## ChromaDB Connection Errors

If the API can't connect to ChromaDB:

```bash
# Check ChromaDB is running
docker-compose ps chromadb

# Check ChromaDB logs
docker-compose logs chromadb

# Restart ChromaDB
docker-compose restart chromadb
```

## Web UI Not Loading

If http://localhost:8080 doesn't load:

```bash
# Check web-manager container
docker-compose ps web-manager
docker-compose logs web-manager

# Rebuild if needed
docker-compose up -d --build web-manager
```

## Reset Everything

To start fresh:

```bash
# Remove all containers, volumes, and project images
./scripts/cleanup.sh

# Or full cleanup including base images
./scripts/cleanup.sh --full

# Start fresh
./scripts/start.sh
```

## Getting Help

If issues persist:

1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:5000/health`
3. Run tests: `./scripts/test.sh`
