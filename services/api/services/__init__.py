"""
Services package initialization

This package contains the core services for Krakenly API:
- embedding: Text embedding using fastembed
- ollama: LLM interaction with Ollama
- chromadb: Vector database operations
- indexing: Text and JSON chunking
- search: Query complexity analysis
"""

# Note: Heavy imports (fastembed, chromadb) are done lazily in each module
# to avoid import errors when testing individual components.
# Use direct imports from submodules:
#   from services.embedding import encode_texts
#   from services.ollama import generate_text

