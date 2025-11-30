# API Reference

This document provides complete API documentation for Krakenly.

## Overview

Krakenly provides two main interfaces:
- **Web Manager** (Port 8080) - Browser-based UI
- **REST API** (Port 5000) - Programmatic access

## Web Manager (Port 8080)

Browser-based interface for managing data and chatting with AI.

**Access at:** http://localhost:8080

### Features

| Feature | Description |
|---------|-------------|
| **Upload files** | Drag & drop or click to upload data |
| **Manage sources** | View and delete indexed data |
| **Semantic search** | Search with auto-optimized query complexity |
| **AI chat** | Conversational interface with markdown formatting |

## REST API (Port 5000)

### Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for all services |
| `/index` | POST | Index data |
| `/index/upload` | POST | Upload and index a file |
| `/sources` | GET | List indexed sources |
| `/sources/<id>` | DELETE | Delete a source |
| `/search` | POST | Semantic search |
| `/search/rag` | POST | RAG-based search with AI response |
| `/generate` | POST | Generate text from prompt |
| `/stats` | GET | Index statistics |
| `/models` | GET | List available models |
| `/models/pull` | POST | Pull a new model |

---

## Endpoint Details

### Health Check

Check the health status of all services.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "api": "ok",
    "chromadb": "ok",
    "ollama": "ok"
  }
}
```

---

### Index Data

Index data with optional metadata.

```http
POST /index
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Document content to index...",
  "metadata": {
    "source": "document-name.txt",
    "type": "documentation"
  }
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Document content to index |
| `metadata` | object | No | Additional metadata |
| `metadata.source` | string | No | Source filename |
| `metadata.type` | string | No | Document type |

**Response:**
```json
{
  "success": true,
  "chunks_indexed": 15,
  "source": "document-name.txt"
}
```

---

### Upload File

Upload and index a file directly.

```http
POST /index/upload
Content-Type: multipart/form-data
```

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload and index |

**Supported Formats:**
- Text files (`.txt`)
- Markdown files (`.md`)
- JSON files (`.json`)

**Example:**
```bash
curl -X POST http://localhost:5000/index/upload \
  -F "file=@document.md"
```

**Response:**
```json
{
  "success": true,
  "chunks_indexed": 42,
  "source": "document.md"
}
```

---

### List Sources

Get all indexed data sources.

```http
GET /sources
```

**Response:**
```json
{
  "sources": [
    {
      "id": "abc123",
      "source": "kubernetes-intro.txt",
      "chunks": 15,
      "indexed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### Delete Source

Delete an indexed data source.

```http
DELETE /sources/<id>
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Source ID to delete |

**Response:**
```json
{
  "success": true,
  "deleted": "abc123"
}
```

---

### Semantic Search

Search indexed data using semantic similarity.

```http
POST /search
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What is Kubernetes?",
  "top_k": 5
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `top_k` | integer | No | 5 | Number of results to return |

**Response:**
```json
{
  "results": [
    {
      "text": "Kubernetes is an open-source container orchestration...",
      "metadata": {
        "source": "kubernetes-intro.txt"
      },
      "score": 0.89
    }
  ],
  "query": "What is Kubernetes?",
  "count": 5
}
```

---

### RAG Search (Chat)

Perform semantic search and generate an AI response based on the results.

> **Note:** This is the primary endpoint for chat interactions. All responses are grounded in your indexed data.

```http
POST /search/rag
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "Explain Kubernetes to me",
  "top_k": 3,
  "max_tokens": 256
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Question to ask |
| `top_k` | integer | No | 3 | Number of context data items |
| `max_tokens` | integer | No | 512 | Maximum response length |

**Response:**
```json
{
  "answer": "Kubernetes is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications...",
  "sources": [
    {
      "text": "Kubernetes is an open-source container orchestration...",
      "metadata": {"source": "kubernetes-intro.txt"},
      "score": 0.89
    }
  ],
  "query": "Explain Kubernetes to me"
}
```

---

### Generate Text

Generate text from a prompt without data context.

```http
POST /generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "What is Docker?",
  "max_tokens": 100
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | Text prompt |
| `max_tokens` | integer | No | 512 | Maximum response length |

**Response:**
```json
{
  "response": "Docker is a platform for developing, shipping, and running applications in containers...",
  "prompt": "What is Docker?"
}
```

---

### Index Statistics

Get statistics about the vector index.

```http
GET /stats
```

**Response:**
```json
{
  "total_documents": 150,
  "total_sources": 5,
  "index_size_mb": 12.5
}
```

---

### List Models

Get available Ollama models.

```http
GET /models
```

**Response:**
```json
{
  "models": [
    {
      "name": "qwen2.5:3b",
      "size": "1.9GB",
      "modified_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### Pull Model

Download a new Ollama model.

```http
POST /models/pull
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "phi3:mini"
}
```

**Response:**
```json
{
  "success": true,
  "model": "phi3:mini"
}
```

---

## Internal Services

These services are used internally and typically don't need direct access:

| Service | Port | Description |
|---------|------|-------------|
| Ollama | 11434 | LLM inference engine |
| ChromaDB | 8000 | Vector database |

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "status": 400
}
```

**Common Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service unavailable |
