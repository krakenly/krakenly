# Krakenly Knowledge Base

## Overview

Krakenly is a fully local, privacy-focused personal AI assistant that runs entirely on your machine using Docker. It is designed to answer questions grounded in your own data rather than relying on generic LLM knowledge. All responses are generated using Retrieval-Augmented Generation (RAG), which means the system first searches your indexed data before generating a response.

## Architecture

The system consists of four containerized services:

### 1. Ollama (LLM Inference)
- **Port**: 11434 (internal)
- **Model**: qwen2.5:3b (3.1 billion parameters, Q4_K_M quantization)
- **Size**: 1.9 GB on disk
- **Purpose**: Generates natural language responses based on retrieved context
- **Performance**: 15-18 tokens/second on CPU (AMD EPYC, 4 cores)

### 2. ChromaDB (Vector Database)
- **Port**: 8000 (internal)
- **Purpose**: Stores data embeddings for semantic search
- **Persistence**: Data stored in Docker volume `chroma_data`

### 3. API Service
- **Port**: 5000 (external)
- **Framework**: Flask with Gunicorn
- **Embedding Model**: BAAI/bge-small-en-v1.5 (via Fastembed, ONNX optimized)
- **Purpose**: Unified REST API for all operations

### 4. Web Manager
- **Port**: 8080 (external)
- **Purpose**: Browser-based UI for data management and AI chat
- **Server**: Nginx

## Key Features

### Data Indexing
- Upload files via drag-and-drop or API
- Supports JSON, Markdown, and plain text
- Enhanced preprocessing with entity extraction and Q&A generation
- Automatic chunking optimized for retrieval

### Semantic Search
- Vector similarity search using embeddings
- Query complexity auto-detection
- Adjustable top_k and max_tokens parameters

### RAG-Based Chat
- All conversations are grounded in indexed data
- No standalone chat mode - ensures responses are based on your data
- Sources cited in responses

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for all services |
| `/index` | POST | Index data with text and metadata |
| `/index/upload` | POST | Upload and index a file |
| `/sources` | GET | List all indexed sources |
| `/sources/<id>` | DELETE | Delete a source and its chunks |
| `/search` | POST | Semantic search (no LLM) |
| `/search/rag` | POST | RAG search with AI response |
| `/generate` | POST | Direct text generation |
| `/stats` | GET | Index statistics |
| `/models` | GET | List available Ollama models |

## Performance Benchmarks

Tested on AMD EPYC 9V74 (4 cores, CPU-only, 32GB RAM):

| Query Type | Context Size | Response Time | Speed |
|------------|--------------|---------------|-------|
| Trivial | 0 chars | 0.6s | 15-17 tok/s |
| Simple | ~500 chars | 3-5s | 12-15 tok/s |
| Medium | ~4000 chars | 20-30s | 4-5 tok/s |
| Complex | ~8000 chars | 40-60s | 4-5 tok/s |

### Performance Notes
- Embedding + vector search: ~15-20ms (negligible)
- LLM inference: 99%+ of response time
- Context size is the main factor affecting speed
- Model warm-up required after container restart (~10-30s first query)

## Hardware Requirements

### Minimum
- 8GB RAM
- 4 CPU cores
- 20GB disk space

### Recommended
- 16GB RAM
- 4+ CPU cores
- 30GB disk space
- GPU (optional, 10-20x faster inference)

## Privacy & Security

- 100% local execution - no data leaves your machine
- No telemetry or external API calls
- Models downloaded from official sources (Ollama, HuggingFace) on first run only
- All data stored in local Docker volumes

## Common Commands

```bash
# Start services
./scripts/start.sh

# Stop services
docker compose down

# View logs
docker compose logs -f api

# Run tests
./scripts/test.sh

# Cleanup
./scripts/cleanup.sh
```

## Design Philosophy

Krakenly is a **personal AI assistant** where all responses are grounded in your indexed data. Unlike general-purpose chatbots, this system:

1. Always searches your data before responding
2. Cites sources in responses
3. Admits when information is not found in the index
4. Prioritizes accuracy over creativity

The goal is to be a reliable knowledge base assistant for your private data, not a general conversationalist.
