import os
import requests
from typing import Optional, Any, Dict, Tuple
from urllib.parse import urlparse
import chromadb
from config import CHROMA_HOST, HEALTH_CHECK_TIMEOUT

# Global instances
_chroma_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None

def init_chromadb() -> Tuple[Optional[chromadb.ClientAPI], Optional[chromadb.Collection]]:
    """
    Initialize ChromaDB client.
    """
    global _chroma_client, _collection
    
    if _chroma_client is None:
        try:
            print(f"Connecting to ChromaDB at: {CHROMA_HOST}")
            # 1. Host parsing WITH restored fallbacks (Fixes "Missing fallbacks" issue)
            parsed = urlparse(CHROMA_HOST)
            chroma_host = parsed.hostname or 'chromadb'
            chroma_port = parsed.port or 8000

            # 2. Removed 'Settings' (Fixes "Feature addition" issue)
            _chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
            
            _collection = _chroma_client.get_or_create_collection(
                name="documents",
                metadata={"description": "Document embeddings for Krakenly"}
            )

            print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            
    return _chroma_client, _collection

def get_client() -> Optional[chromadb.ClientAPI]:
    """Get the ChromaDB client singleton"""
    if _chroma_client is None:
        init_chromadb()
    return _chroma_client

def get_collection() -> Optional[chromadb.Collection]:
    """Get the documents collection singleton"""
    global _collection
    if _collection is None:
        init_chromadb()
    return _collection

def check_health() -> Dict[str, Any]:
    """
    Check if ChromaDB is running.
    RESTORED: Original implementation using requests and timeout.
    """
    try:
        # 3. Restored requests.get with timeout (Fixes "Semantic change" issue)
        # Note: Using v2 endpoint as seen in original code snippets
        resp = requests.get(f"{CHROMA_HOST}/api/v2/heartbeat", timeout=HEALTH_CHECK_TIMEOUT)
        return {'running': resp.status_code == 200}
    except Exception:
        return {'running': False}
        
