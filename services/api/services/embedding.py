"""
Embedding service for Krakenly API
Handles text embedding using fastembed
"""
from fastembed import TextEmbedding
from config import EMBEDDING_MODEL

# Global embedder instance
_embedder = None


def get_embedder():
    """Get or initialize the embedder singleton"""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedder


def init_embedder():
    """Initialize the embedding model"""
    global _embedder
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
    print("Embedding model loaded successfully")
    return _embedder


def encode_texts(texts):
    """
    Generate embeddings for a list of texts using fastembed.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors as lists of floats
    """
    embedder = get_embedder()
    embeddings = list(embedder.embed(texts))
    return [embedding.tolist() for embedding in embeddings]
