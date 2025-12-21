"""
ChromaDB service for Krakenly API
Handles connection to ChromaDB vector database
"""
from typing import Dict, Tuple, Any, Optional
from urllib.parse import urlparse
import chromadb # type: ignore
from config import CHROMA_HOST, HEALTH_CHECK_TIMEOUT
import requests

# Global ChromaDB client and collection
_chroma_client: Optional[Any] = None
_collection: Optional[Any] = None


def get_client() -> Any:
    """Get the ChromaDB client singleton"""
    global _chroma_client
    if _chroma_client is None:
        init_chromadb()
    return _chroma_client


def get_collection() -> Any:
    """Get the documents collection singleton"""
    global _collection
    if _collection is None:
        init_chromadb()
    return _collection


def init_chromadb() -> Tuple[Any, Any]:
    """
    Initialize ChromaDB client and collection.
    
    Returns:
        tuple: (client, collection)
    """
    global _chroma_client, _collection
    
    print(f"Connecting to ChromaDB at: {CHROMA_HOST}")
    
    # Parse host and port from CHROMA_HOST (e.g., "http://chromadb:8000")
    parsed = urlparse(CHROMA_HOST)
    chroma_host: str = parsed.hostname or 'chromadb'
    chroma_port: int = parsed.port or 8000
    
    _chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    
    _collection = _chroma_client.get_or_create_collection(
        name="documents",
        metadata={"description": "Document embeddings for Krakenly"}
    )
    
    print(f"Connected to ChromaDB, collection has {_collection.count()} documents")
    
    return _chroma_client, _collection


def check_health() -> Dict[str, bool]:
    """
    Check ChromaDB health status.
    
    Returns:
        dict: Health status with 'running' field
    """
    try:
        resp = requests.get(f"{CHROMA_HOST}/api/v2/heartbeat", timeout=HEALTH_CHECK_TIMEOUT)
        return {'running': resp.status_code == 200}
    except Exception:
        return {'running': False}