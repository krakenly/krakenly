"""
Index metadata management for Krakenly API
Handles tracking of indexed document sources
"""
import os
import json
from config import INDEX_METADATA_FILE

# Global index metadata
_index_metadata = {}


def get_metadata():
    """Get the current index metadata"""
    global _index_metadata
    return _index_metadata


def load_metadata():
    """
    Load index metadata from file.
    
    Returns:
        dict: The loaded metadata
    """
    global _index_metadata
    try:
        if os.path.exists(INDEX_METADATA_FILE):
            with open(INDEX_METADATA_FILE, 'r') as f:
                _index_metadata = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load index metadata: {e}")
        _index_metadata = {}
    return _index_metadata


def save_metadata():
    """Save index metadata to file"""
    global _index_metadata
    try:
        os.makedirs(os.path.dirname(INDEX_METADATA_FILE), exist_ok=True)
        with open(INDEX_METADATA_FILE, 'w') as f:
            json.dump(_index_metadata, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save index metadata: {e}")


def add_source(source_id, chunks, size_bytes, metadata=None):
    """
    Add or update a source in the metadata.
    
    Args:
        source_id: Unique identifier for the source
        chunks: Number of chunks indexed
        size_bytes: Size of the original content
        metadata: Additional metadata dict
    """
    from datetime import datetime
    
    global _index_metadata
    _index_metadata[source_id] = {
        'source': source_id,
        'chunks': chunks,
        'size_bytes': size_bytes,
        'indexed_at': datetime.utcnow().isoformat(),
        'metadata': metadata or {}
    }
    save_metadata()


def remove_source(source_id):
    """
    Remove a source from the metadata.
    
    Args:
        source_id: Source to remove
        
    Returns:
        bool: True if removed, False if not found
    """
    global _index_metadata
    if source_id in _index_metadata:
        del _index_metadata[source_id]
        save_metadata()
        return True
    return False


def list_sources():
    """
    Get all sources sorted by indexed_at descending.
    
    Returns:
        list: List of source dicts
    """
    global _index_metadata
    sources = []
    for source_id, meta in _index_metadata.items():
        sources.append({
            'source': source_id,
            'chunks': meta.get('chunks', 0),
            'size_bytes': meta.get('size_bytes', 0),
            'indexed_at': meta.get('indexed_at', ''),
            'metadata': meta.get('metadata', {})
        })
    
    sources.sort(key=lambda x: x.get('indexed_at', ''), reverse=True)
    return sources
