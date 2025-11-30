# 🐙 Krakenly

[![GitHub](https://img.shields.io/badge/GitHub-Krakenly-blue?logo=github)](https://github.com/krakenly/krakenly)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Your data. Your AI. Your machine.**

A fully local, privacy-focused AI assistant that runs entirely on your machine using Docker. Perfect for personal home servers, NAS devices, or any always-on machine. Unlike cloud-based AI services, Krakenly keeps all your data private—nothing ever leaves your machine.

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

Krakenly is a **Retrieval-Augmented Generation (RAG)** system that lets you chat with your own data. Upload any text, markdown, or JSON files, and the AI will answer questions based specifically on your content rather than generic knowledge. Think of it as having a personal research assistant that has read and understood all your data.

### How it works

1. **Index your data** - Upload files through the web interface or API
2. **Ask questions** - The system searches your data for relevant context
3. **Get grounded answers** - The AI generates responses based on your data, citing sources

### Key difference from cloud-based AI

Cloud AI services answer from their training data. Krakenly answers from **your data**. If the information isn't in your indexed data, it will tell you rather than making something up. Plus, your data never leaves your machine.

## Components

This system uses **official images** for maximum reliability and minimal footprint:

- **Ollama**: Official `ollama/ollama` image for LLM inference (`qwen2.5:3b`)
- **ChromaDB**: Official `chromadb/chroma` image for vector storage
- **API Service**: Modular REST API with Fastembed embeddings (`bge-small-en-v1.5`)
- **Web Manager**: Browser-based UI for data management and AI chat

## Features

- 🔒 **100% Local**: All services run on your machine - no data leaves your system
- 🏠 **Home Server Ready**: Perfect for NAS, Raspberry Pi, or any always-on machine
- ⚡ **Optimized**: Official images, ONNX embeddings, efficient LLM inference
- 🤖 **Local LLM**: Uses Ollama with quantized models (`qwen2.5:3b` by default)
- 🔍 **Semantic Search**: Find relevant data using vector similarity
- 📚 **RAG Support**: Context-aware AI responses using your indexed data
- 🧠 **Smart Preprocessing**: Enhanced data chunking with entity extraction, relationships, and Q&A formatting
- 🌐 **Web Interface**: Browser-based UI for file uploads, search, and AI chat
- 🐳 **Containerized**: All services run as Docker containers
- 💾 **Persistent Storage**: Your indexed data and models persist across restarts

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
./scripts/install-docker-prereqs.sh
```

This script will:
- ✅ Check system requirements (RAM, CPU, disk space)
- ✅ Install Docker (if not present)
- ✅ Install Docker Compose (if not present)
- ✅ Configure Docker permissions

**Note:** If Docker is newly installed, log out and back in for group permissions to take effect.

## Quick Start

There are two ways to run Krakenly:

### Option 1: Quick Start (Recommended)

The fastest way to get started. Uses pre-built images from DockerHub:

```bash
# Clone the repository
git clone https://github.com/krakenly/krakenly.git
cd krakenly

# Install prerequisites and start (one command!)
./scripts/start-docker.sh
```

This will:
- Install Docker and Docker Compose (if needed)
- Pull official images from DockerHub
- Start all services
- Run health checks and tests

Open http://localhost:8080 to access the Web UI.

### Option 2: Build from Source (For Development)

If you want to modify the code or contribute:

```bash
# Clone the repository
git clone https://github.com/krakenly/krakenly.git
cd krakenly

# Build from source and start
./scripts/start-docker-dev.sh
```

This will:
- Install prerequisites (Docker, Docker Compose)
- Build Docker images locally from source
- Start all services (Ollama, ChromaDB, Krakenly)
- Wait for health checks to pass
- Pull the `qwen2.5:3b` model if not present
- Run end-to-end tests automatically

**Note:** First startup downloads the `qwen2.5:3b` model (~1.9GB). Subsequent starts are instant.

### Option 3: Kubernetes Deployment

Deploy to a Kubernetes cluster:

```bash
# Clone the repository
git clone https://github.com/krakenly/krakenly.git
cd krakenly

# Deploy all components
kubectl apply -k k8s/

# Wait for pods to be ready
kubectl -n krakenly wait --for=condition=ready pod -l app.kubernetes.io/part-of=krakenly --timeout=300s

# Port forward to access locally
kubectl -n krakenly port-forward svc/krakenly 8080:80
```

See [k8s/README.md](k8s/README.md) for detailed Kubernetes configuration options.

### 3. Verify Services

```bash
curl http://localhost:5000/health
```

### 4. Run Tests

```bash
./scripts/test.sh
```

This runs an end-to-end test that:
- Indexes sample data
- Performs semantic search
- Tests RAG query
- Verifies AI generation

## Usage

### Web Interface (Recommended)

Open **http://localhost:8080** in your browser to:

- **Upload data** - Drag & drop files to index them
- **Manage sources** - View and delete indexed data
- **Search** - Semantic search across your data
- **Chat** - Ask questions and get AI responses grounded in your data

### API Examples

```bash
# Index your data
curl -X POST http://localhost:5000/index \
  -H "Content-Type: application/json" \
  -d '{"text": "Your data content...", "metadata": {"source": "doc.txt"}}'

# Search data
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is...?", "top_k": 5}'

# Chat with AI (uses RAG)
curl -X POST http://localhost:5000/search/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain this to me", "max_tokens": 256}'
```

> **Note:** All chat interactions use RAG to ground responses in your indexed data.

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API.md) | Complete REST API documentation |
| [Configuration](docs/CONFIGURATION.md) | Environment variables and model options |
| [Data Preprocessing](docs/PREPROCESSING.md) | How data is chunked for search |
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
# Docker Compose - Quick start (uses DockerHub images)
./scripts/start-docker.sh

# Docker Compose - Development (builds from source)
./scripts/start-docker-dev.sh

# Kubernetes - Deploy to cluster (uses DockerHub images)
./scripts/deploy-k8s.sh

# Kubernetes - Local development (builds + minikube)
./scripts/deploy-k8s-local.sh

# Install Docker prerequisites
./scripts/install-docker-prereqs.sh

# Install Kubernetes prerequisites
./scripts/install-k8s-prereqs.sh

# Stop Docker Compose services
docker-compose down

# View logs
docker-compose logs -f

# Cleanup Docker
./scripts/cleanup-docker.sh

# Cleanup Kubernetes
./scripts/cleanup-k8s.sh

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
│   ├── install-docker-prereqs.sh # Install Docker & Docker Compose
│   ├── install-k8s-prereqs.sh    # Install kubectl & minikube
│   ├── start-docker.sh           # Docker Compose (DockerHub images)
│   ├── start-docker-dev.sh       # Docker Compose (build from source)
│   ├── deploy-k8s.sh             # Kubernetes (DockerHub images)
│   ├── deploy-k8s-local.sh       # Kubernetes (build + minikube)
│   ├── cleanup-docker.sh         # Cleanup Docker resources
│   ├── cleanup-k8s.sh            # Cleanup Kubernetes resources
│   ├── test.sh
│   └── benchmark.py
├── services/
│   ├── api/                # REST API service
│   └── web-manager/        # Browser UI
├── tests/
│   └── sample_data.md
└── examples/
    └── basic_usage.py
```

---

**Acknowledgments:** [Ollama](https://ollama.ai/), [Fastembed](https://github.com/qdrant/fastembed), [ChromaDB](https://www.trychroma.com/)
