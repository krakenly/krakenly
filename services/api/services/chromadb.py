import os
from typing import Optional, Any, Dict, Tuple
from urllib.parse import urlparse
import chromadb
from chromadb.config import Settings
from config import CHROMA_HOST

# Global instances
_chroma_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None

def init_chromadb() -> Tuple[chromadb.ClientAPI, chromadb.Collection]:
    """
    Initialize ChromaDB client.
    Restored original return type (tuple) and logic.
    """
    global _chroma_client, _collection
    
    # 1. Host parsing (Kept correct from previous fix)
    parsed = urlparse(CHROMA_HOST)
    chroma_host = parsed.hostname
    chroma_port = parsed.port

    _chroma_client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # 2. Hardcoded "documents" collection (Fixes "get_collection signature" issue)
    _collection = _chroma_client.get_or_create_collection(
        name="documents",
        metadata={"description": "Document embeddings for Krakenly"}
    )

    print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
    
    # 3. Return tuple (Fixes "init_chromadb return type" issue)
    return _chroma_client, _collection

def get_client() -> Optional[chromadb.ClientAPI]:
    """Get the ChromaDB client singleton"""
    if _chroma_client is None:
        init_chromadb()
    return _chroma_client

def get_collection() -> Optional[chromadb.Collection]:
    """
    Get the documents collection singleton.
    RESTORED: No arguments. Always returns 'documents' collection.
    """
    global _collection
    if _collection is None:
        init_chromadb()
    return _collection

def check_health() -> Dict[str, Any]:
    """
    Check if ChromaDB is running.
    RESTORED: Name is 'check_health' (not check_heartbeat).
    RESTORED: Return format is {'running': bool}.
    """
    client = get_client()
    if client:
        try:
            client.heartbeat()
            # Fixes "Return value structure changed" issue
            return {'running': True}
        except Exception as e:
            return {'running': False}
    return {'running': False}
