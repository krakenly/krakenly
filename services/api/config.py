"""
Configuration module for Krakenly API
Centralizes all environment variables and settings
"""
import os

# External service endpoints
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
CHROMA_HOST = os.getenv('CHROMA_HOST', 'http://chromadb:8000')

# Model configuration
MODEL_NAME = os.getenv('MODEL_NAME', 'qwen2.5:3b')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')

# Data paths
INDEX_METADATA_FILE = os.getenv('INDEX_METADATA_FILE', '/data/index_metadata.json')

# Chunking defaults
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
MAX_JSON_CHUNK_SIZE = 800  # Reduced for faster CPU inference

# RAG context limits (for CPU performance)
MAX_CONTEXT_CHARS = 3000  # Max chars to send to LLM
MAX_CONTEXT_CHUNKS = 3    # Max chunks to retrieve

# Request timeouts
OLLAMA_TIMEOUT = 300  # 5 minutes
OLLAMA_PULL_TIMEOUT = 600  # 10 minutes
HEALTH_CHECK_TIMEOUT = 2

# Model warmup settings
WARMUP_MAX_RETRIES = 30
WARMUP_RETRY_DELAY = 2  # seconds
