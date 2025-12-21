"""
ChromaDB service for Krakenly API
Handles vector database operations
"""
from typing import Dict, Any, Optional, TYPE_CHECKING
from config import CHROMA_HOST, HEALTH_CHECK_TIMEOUT
import requests

if TYPE_CHECKING:
    import chromadb

# Global ChromaDB client and collection
_chroma_client: Optional["chromadb.ClientAPI"] = None
_collection: Optional["chromadb.Collection"] = None


def get_client() -> Optional["chromadb.ClientAPI"]:
    """
    Get or create the ChromaDB client.
    
    Returns:
        The ChromaDB client instance
    """
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            _chroma_client = chromadb.HttpClient(host=CHROMA_HOST.split(':')[0], port=8000)
        except Exception as e:
            print(f"Error connecting to ChromaDB: {e}")
            _chroma_client = None
    return _chroma_client


def get_collection() -> Optional["chromadb.Collection"]:
    """
    Get or create the document collection.
    
    Returns:
        The ChromaDB collection
    """
    global _collection
    client = get_client()
    if _collection is None and client:
        try:
            _collection = client.get_or_create_collection(name="documents")
        except Exception as e:
            print(f"Error getting collection: {e}")
    return _collection


def check_health() -> Dict[str, Any]:
    """
    Check if ChromaDB is responsive.
    
    Returns:
        dict: Health status
    """
    try:
        # Check if we can connect to the API
        resp = requests.get(f"http://{CHROMA_HOST.split(':')[0]}:8000/api/v1/heartbeat", timeout=HEALTH_CHECK_TIMEOUT)
        return {'running': resp.status_code == 200}
    except Exception:
        return {'running': False}
    