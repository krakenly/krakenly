# 🦑 Krakenly

[![GitHub](https://img.shields.io/badge/GitHub-Krakenly-blue?logo=github)](https://github.com/krakenly/krakenly)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your documents. Your AI. Your machine.**

A fully local, privacy-focused AI assistant that runs entirely on your machine using Docker. Unlike cloud-based AI services, Krakenly keeps all your data private—nothing ever leaves your machine.

## Table of Contents

- [What is this?](#what-is-this)
- [Components](#components)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Documentation](#documentation)
- [Common Commands](#common-commands)
- [Project Structure](#project-structure)
- [License](#license)

## What is this?

Krakenly is a **Retrieval-Augmented Generation (RAG)** system that lets you chat with your own documents. Upload any text, markdown, or JSON files, and the AI will answer questions based specifically on your content rather than generic knowledge. Think of it as having a personal research assistant that has read and understood all your documents.

### How it works

1. **Index your documents** - Upload files through the web interface or API
2. **Ask questions** - The system searches your documents for relevant context
3. **Get grounded answers** - The AI generates responses based on your data, citing sources

### Key difference from cloud-based AI

Cloud AI services answer from their training data. Krakenly answers from **your documents**. If the information isn't in your indexed files, it will tell you rather than making something up. Plus, your data never leaves your machine.

## Components

This system uses **official images** for maximum reliability and minimal footprint:

- **Ollama**: Official `ollama/ollama` image for LLM inference (`qwen2.5:3b`)
- **ChromaDB**: Official `chromadb/chroma` image for vector storage
- **API Service**: Modular REST API with Fastembed embeddings (`bge-small-en-v1.5`)
- **Web Manager**: Browser-based UI for document management and AI chat

## Features

- 🔒 **100% Local**: All services run on your machine - no data leaves your system
- ⚡ **Optimized**: Official images, ONNX embeddings, efficient LLM inference
- 🤖 **Local LLM**: Uses Ollama with quantized models (`qwen2.5:3b` by default)
- 🔍 **Semantic Search**: Find relevant documents using vector similarity
- 📚 **RAG Support**: Context-aware AI responses using your indexed documents
- 🧠 **Smart Preprocessing**: Enhanced document chunking with entity extraction, relationships, and Q&A formatting
- 🌐 **Web Interface**: Browser-based UI for file uploads, search, and AI chat
- 🐳 **Containerized**: All services run as Docker containers (~4.9GB total)
- 💾 **Persistent Storage**: Your indexed documents and models persist across restarts

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Docker Compose                          │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────┐  │
│  │    Ollama    │  │   ChromaDB   │  │    API     │  │ Web  │  │
│  │   (official) │  │   (official) │  │  Service   │  │ UI   │  │
│  │              │  │              │  │            │  │      │  │
│  │  LLM Engine  │  │ Vector Store │  │ Fastembed  │  │nginx │  │
│  │ qwen2.5:3b   │  │              │  │  REST API  │  │      │  │
│  └──────────────┘  └──────────────┘  └────────────┘  └──────┘  │
│         │                 │                │              │    │
│  ┌──────┴─────────────────┴────────────────┴──────────────┴─┐  │
│  │                     Docker Volumes                       │  │
│  │              (ollama_data & chroma_data)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker**: Container runtime
- **Docker Compose**: Container orchestration
- **Hardware**: 
  - Minimum: 8GB RAM, 2 CPU cores, 10GB disk space
  - Recommended: 12GB+ RAM, 4+ CPU cores, 20GB disk space

> **Note:** The `qwen2.5:3b` model requires ~4GB RAM during inference. Systems with less than 8GB RAM may experience slow performance or out-of-memory errors.

### Automated Installation

Run the prerequisites installer:

```bash
./scripts/install-prerequisites.sh
```

This script will:
- ✅ Check system requirements (RAM, CPU, disk space)
- ✅ Install Docker (if not present)
- ✅ Install Docker Compose (if not present)
- ✅ Configure Docker permissions

**Note:** If Docker is newly installed, log out and back in for group permissions to take effect.

## Quick Start

### 1. Install Prerequisites

```bash
./scripts/install-prerequisites.sh
```

### 2. Start Services

```bash
./scripts/start.sh
```

This will:
- Build all Docker images (first run takes 5-10 minutes)
- Start all three services
- Wait for health checks to pass
- Pull the `qwen2.5:3b` model if not present
- Run end-to-end tests automatically
- Display service endpoints

**Note:** First startup downloads the `qwen2.5:3b` model (~1.9GB). Subsequent starts are instant.

### 3. Verify Services

```bash
curl http://localhost:5000/health
```

### 4. Run Tests

```bash
./scripts/test.sh
```

This runs an end-to-end test that:
- Indexes a sample document
- Performs semantic search
- Tests RAG query
- Verifies AI generation

## Usage

### Web Interface (Recommended)

Open **http://localhost:8080** in your browser to:

- **Upload documents** - Drag & drop files to index them
- **Manage sources** - View and delete indexed documents
- **Search** - Semantic search across your documents
- **Chat** - Ask questions and get AI responses grounded in your data

### API Examples

```bash
# Index a document
curl -X POST http://localhost:5000/index \
  -H "Content-Type: application/json" \
  -d '{"text": "Your document content...", "metadata": {"source": "doc.txt"}}'

# Search documents
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is...?", "top_k": 5}'

# Chat with AI (uses RAG)
curl -X POST http://localhost:5000/search/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain this to me", "max_tokens": 256}'
```

> **Note:** All chat interactions use RAG to ground responses in your indexed documents.

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API.md) | Complete REST API documentation |
| [Configuration](docs/CONFIGURATION.md) | Environment variables and model options |
| [Document Preprocessing](docs/PREPROCESSING.md) | How documents are chunked for search |
| [Performance Benchmarks](docs/BENCHMARKS.md) | Response times and throughput metrics |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |

### Quick Reference

| Service | Port | Description |
|---------|------|-------------|
| Web UI | 8080 | Browser interface |
| API | 5000 | REST endpoints |
| Ollama | 11434 | LLM (internal) |
| ChromaDB | 8000 | Vectors (internal) |

## Common Commands

```bash
# Install prerequisites (Docker, Docker Compose)
./scripts/install-prerequisites.sh

# Start services
./scripts/start.sh

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Cleanup (remove containers, volumes, images)
./scripts/cleanup.sh

# Run tests
./scripts/test.sh

# Run benchmark
python scripts/benchmark.py
```

## Project Structure

```
ai-assistant/
├── docker-compose.yml      # Container orchestration
├── docs/                   # Documentation
│   ├── API.md              # API reference
│   ├── BENCHMARKS.md       # Performance metrics
│   ├── CONFIGURATION.md    # Configuration options
│   ├── PREPROCESSING.md    # Document processing
│   └── TROUBLESHOOTING.md  # Common issues
├── scripts/
│   ├── install-prerequisites.sh
│   ├── start.sh
│   ├── test.sh
│   ├── cleanup.sh
│   └── benchmark.py
├── services/
│   ├── api/                # REST API service
│   └── web-manager/        # Browser UI
├── tests/
│   └── sample_data.md
└── examples/
    └── basic_usage.py
```

## License

See LICENSE file.

---

**Acknowledgments:** [Ollama](https://ollama.ai/), [Fastembed](https://github.com/qdrant/fastembed), [ChromaDB](https://www.trychroma.com/)
