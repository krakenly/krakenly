import os
from typing import Optional, Any, Dict
from urllib.parse import urlparse
import chromadb
from chromadb.config import Settings
from config import CHROMA_HOST

# Global instances with Type Hints
_chroma_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None

def init_chromadb() -> None:
    """
    Initialize ChromaDB client.
    Restored original logic using urlparse for safe host extraction.
    """
    global _chroma_client
    if _chroma_client is None:
        try:
            # RESTORED: Use urllib.parse as requested
            parsed = urlparse(CHROMA_HOST)
            chroma_host = parsed.hostname
            chroma_port = parsed.port

            _chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=Settings(anonymized_telemetry=False)
            )
            print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")

def get_client() -> Optional[chromadb.ClientAPI]:
    """Get the ChromaDB client singleton"""
    if _chroma_client is None:
        init_chromadb()
    return _chroma_client

def get_collection(name: str) -> Optional[chromadb.Collection]:
    """Get a specific collection with type hints"""
    global _collection
    client = get_client()
    if client and _collection is None:
        try:
            _collection = client.get_or_create_collection(name=name)
        except Exception as e:
            print(f"Error getting collection {name}: {e}")
    return _collection

def check_heartbeat() -> Dict[str, Any]:
    """Check if ChromaDB is running"""
    client = get_client()
    if client:
        try:
            # RESTORED: Changed back to v2 as requested
            client.heartbeat()
            return {"status": "ok", "service": "chromadb-v2"}
        except Exception as e:
            return {"status": "error", "details": str(e)}
    return {"status": "disconnected"}
    
