"""
Configuration module for Krakenly API
Centralizes all environment variables and settings
"""
import os

# External service endpoints
OLLAMA_HOST: str = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
CHROMA_HOST: str = os.getenv('CHROMA_HOST', 'http://chromadb:8000')

# Model configuration
MODEL_NAME: str = os.getenv('MODEL_NAME', 'qwen2.5:3b')
EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')

# Data paths
INDEX_METADATA_FILE: str = os.getenv('INDEX_METADATA_FILE', '/data/index_metadata.json')

# Chunking defaults
DEFAULT_CHUNK_SIZE: int = 500
DEFAULT_CHUNK_OVERLAP: int = 50
MAX_JSON_CHUNK_SIZE: int = 800  # Reduced for faster CPU inference

# RAG context limits (for CPU performance)
MAX_CONTEXT_CHARS: int = 3000  # Max chars to send to LLM
MAX_CONTEXT_CHUNKS: int = 3    # Max chunks to retrieve

# Request timeouts
OLLAMA_TIMEOUT: int = 300  # 5 minutes
OLLAMA_PULL_TIMEOUT: int = 600  # 10 minutes
HEALTH_CHECK_TIMEOUT: int = 2

# Model warmup settings
WARMUP_MAX_RETRIES: int = 30
WARMUP_RETRY_DELAY: int = 2  # seconds
