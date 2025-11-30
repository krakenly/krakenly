# Data Preprocessing

This document explains how Krakenly processes and chunks data for optimal search accuracy.

## Overview

When you upload data, the system doesn't store it as a single block. Instead, it processes the content into multiple specialized chunks, each optimized for different types of queries. This approach ensures that searches match regardless of how the query is phrased.

## Why Chunking Matters

Traditional search requires exact keyword matches. Semantic search improves this by understanding meaning, but chunk quality dramatically affects results:

| Approach | Pros | Cons |
|----------|------|------|
| **No chunking** | Simple | Long content overwhelms context |
| **Fixed-size chunks** | Predictable | May split mid-sentence |
| **Smart chunking** | Semantic boundaries | More complex |
| **Multi-view chunking** | ✅ Best retrieval | More storage |

This system uses **multi-view chunking** - creating multiple representations of the same content.

---

## JSON Data Processing

JSON data is processed into 6 different chunk types:

### 1. Overview Chunk

A summary of the data structure:

```
Document: config.json
Structure: 3 top-level keys, 15 total values
Keys: settings, users, permissions
```

**Matches queries like:**
- "What's in the config file?"
- "Describe the JSON structure"

### 2. Schema Chunk

Human-readable type descriptions:

```
settings (object):
  - theme: string
  - language: string
  - notifications: boolean
users (array of objects):
  - Each has: name, email, role
```

**Matches queries like:**
- "What fields are in settings?"
- "What type is notifications?"

### 3. Entity Chunks

Each named object gets its own chunk with full path context:

```
Entity: users[0]
Path: users → [0]
Properties:
  - name: "Alice"
  - email: "alice@example.com"
  - role: "admin"
```

**Matches queries like:**
- "Who is Alice?"
- "What's Alice's email?"

### 4. Relationship Chunks

Parent-child and reference mappings:

```
Relationships in config.json:
- settings contains: theme, language, notifications
- users contains 3 user objects
- permissions references user roles
```

**Matches queries like:**
- "What does settings contain?"
- "How are users and permissions related?"

### 5. Index Chunks

Flattened key-value pairs for exact matching:

```
settings.theme = "dark"
settings.language = "en"
settings.notifications = true
users[0].name = "Alice"
users[0].email = "alice@example.com"
```

**Matches queries like:**
- "What is the theme?"
- "dark" (exact value search)

### 6. Q&A Chunks

Pre-formatted question-answer pairs:

```
Q: What is settings.theme?
A: The value of settings.theme is "dark"

Q: List all users
A: The users are: Alice, Bob, Charlie
```

**Matches queries like:**
- "What is the theme setting?"
- "List all users"

---

## Text/Markdown Data Processing

Text and Markdown data is processed into 3 chunk types:

### 1. Summary Chunk

Document statistics and preview:

```
Document: README.md
Words: 1,250
Lines: 180
Preview: "# Project Name\n\nThis project provides..."
```

### 2. Section Chunks

Content split by headers with context:

```
Section: Installation
Parent: Getting Started
Content:
  To install the package, run:
  npm install my-package
```

**For Markdown, sections are split by:**
- `#` H1 headers
- `##` H2 headers
- `###` H3 headers

**For plain text:**
- Blank lines
- Fixed chunk size (~500 tokens)

### 3. Definition Chunks

Extracted "X is a Y" patterns as Q&A:

```
Q: What is Docker?
A: Docker is a platform for developing, shipping, and running applications in containers.

Q: What is Kubernetes?
A: Kubernetes is an open-source container orchestration platform.
```

---

## Chunk Size and Overlap

### Default Settings

| Parameter | Value | Description |
|-----------|-------|-------------|
| Target chunk size | ~500 tokens | Optimal for context windows |
| Overlap | 50 tokens | Prevents split-context issues |
| Max chunk size | 1000 tokens | Hard limit |

### Why These Values?

- **500 tokens**: Large enough for context, small enough for precise retrieval
- **50 token overlap**: Ensures sentences at boundaries aren't lost
- **1000 token max**: Prevents overly long chunks that dilute relevance

---

## Example: Processing a JSON Config

Given this input:

```json
{
  "app": {
    "name": "MyApp",
    "version": "1.0.0"
  },
  "database": {
    "host": "localhost",
    "port": 5432
  }
}
```

The system generates:

| Chunk Type | Count | Example Content |
|------------|-------|-----------------|
| Overview | 1 | "Document with 2 top-level keys: app, database" |
| Schema | 1 | "app (object): name, version; database (object): host, port" |
| Entity | 2 | One for `app`, one for `database` |
| Relationship | 1 | "app contains name, version; database contains host, port" |
| Index | 4 | "app.name = MyApp", "database.port = 5432", etc. |
| Q&A | 4 | "What is app.name? → MyApp", etc. |
| **Total** | **13** | Multiple views of the same data |

---

## Example: Processing Markdown Data

Given data with 3 sections and 2 definitions:

| Chunk Type | Count | Example Content |
|------------|-------|-----------------|
| Summary | 1 | "500 words, 80 lines, preview..." |
| Section | 3 | Each section as separate chunk |
| Definition | 2 | Extracted "X is Y" patterns |
| **Total** | **6** | |

---

## Benefits of Multi-View Chunking

### 1. Query Flexibility

Different query styles match different chunk types:

| Query Style | Best Chunk Type |
|-------------|-----------------|
| "What is X?" | Q&A chunks |
| "Describe the structure" | Schema/Overview |
| Exact value search | Index chunks |
| "How are X and Y related?" | Relationship chunks |

### 2. Improved Recall

Multiple representations increase chances of matching:

- Query: "database port"
- Matches: Index chunk (`database.port = 5432`), Entity chunk (database object), Q&A chunk ("What is the database port?")

### 3. Better Ranking

When multiple chunk types match, the most relevant rises to the top based on semantic similarity.

---

## Storage Considerations

Multi-view chunking increases storage:

| Original Size | Chunks | Approximate Storage |
|---------------|--------|---------------------|
| 1 KB JSON | 10-20 | 5-10 KB |
| 10 KB JSON | 50-100 | 25-50 KB |
| 100 KB Markdown | 100-200 | 100-200 KB |

The ChromaDB vector database efficiently stores embeddings (~1.5KB per chunk for 384-dimension vectors).

---

## Customization

### Disabling Chunk Types

Currently, all chunk types are generated automatically. Future versions may allow configuration:

```yaml
# Proposed future configuration
preprocessing:
  json:
    overview: true
    schema: true
    entities: true
    relationships: false  # Disable
    index: true
    qa: true
```

### Custom Chunking Logic

The preprocessing logic is in `services/api/services/indexing.py`. You can modify chunk generation by editing this file and rebuilding the API service.
