"""
Pytest fixtures for Krakenly tests.
Provides mocked services for unit testing.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))


@pytest.fixture
def app():
    """Create Flask test app with mocked services."""
    with patch('services.embedding.init_embedder'), \
         patch('services.chromadb.init_chromadb'), \
         patch('services.ollama.warmup_ollama_model'), \
         patch('utils.metadata.load_metadata'):
        
        from app import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_chromadb_results():
    """Mock ChromaDB query results."""
    return {
        'ids': [['doc1_0', 'doc1_1']],
        'documents': [['First chunk of text.', 'Second chunk of text.']],
        'metadatas': [[{'source': 'doc1.md'}, {'source': 'doc1.md'}]],
        'distances': [[0.1, 0.2]]
    }


@pytest.fixture
def mock_ollama_stream_response():
    """Mock streaming response lines from Ollama."""
    return [
        b'{"model":"qwen2.5:3b","response":"The","done":false}',
        b'{"model":"qwen2.5:3b","response":" answer","done":false}',
        b'{"model":"qwen2.5:3b","response":" is","done":false}',
        b'{"model":"qwen2.5:3b","response":" 42","done":false}',
        b'{"model":"qwen2.5:3b","response":".","done":true,"eval_count":5,"eval_duration":500000000}'
    ]


@pytest.fixture
def mock_encode_texts():
    """Mock embedding function."""
    def _encode(texts):
        return [[0.1] * 384 for _ in texts]
    return _encode
