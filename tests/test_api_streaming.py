"""
Unit tests for streaming API endpoint.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))


def parse_sse_response(response_data):
    """Parse SSE response into list of events."""
    events = []
    text = response_data.decode('utf-8') if isinstance(response_data, bytes) else response_data
    
    for line in text.split('\n'):
        if line.startswith('data: '):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    
    return events


class TestSearchRagStream:
    """Tests for /search/rag/stream endpoint."""
    
    def test_returns_sse_content_type(self, client):
        """Test that response has correct content type."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_stream.return_value = iter([
                'data: {"type": "token", "content": "Hi"}\n\n',
                {'full_response': 'Hi', 'eval_count': 1}
            ])
            
            response = client.post('/search/rag/stream',
                json={'query': 'Hello'},
                content_type='application/json'
            )
            
            assert 'text/event-stream' in response.content_type
            assert response.headers.get('Cache-Control') == 'no-cache'
            assert response.headers.get('X-Accel-Buffering') == 'no'
    
    def test_start_event_contains_sources(self, client, mock_chromadb_results):
        """Test that start event includes sources."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_coll.return_value.query.return_value = mock_chromadb_results
            mock_stream.return_value = iter([
                'data: {"type": "token", "content": "Test"}\n\n',
                {'full_response': 'Test', 'eval_count': 1}
            ])
            
            response = client.post('/search/rag/stream',
                json={'query': 'What is in doc1?'},
                content_type='application/json'
            )
            
            events = parse_sse_response(response.data)
            
            start_event = next(e for e in events if e['type'] == 'start')
            assert 'sources' in start_event
            assert 'doc1.md' in start_event['sources']
            assert 'activity_id' in start_event
    
    def test_done_event_contains_timings(self, client):
        """Test that done event includes timing information."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_stream.return_value = iter([
                'data: {"type": "token", "content": "Response"}\n\n',
                {'full_response': 'Response', 'eval_count': 1, 'eval_duration': 100000000}
            ])
            
            response = client.post('/search/rag/stream',
                json={'query': 'Test'},
                content_type='application/json'
            )
            
            events = parse_sse_response(response.data)
            
            done_event = next(e for e in events if e['type'] == 'done')
            assert 'timings' in done_event
            assert 'total_ms' in done_event['timings']
            assert 'full_response' in done_event
    
    def test_missing_query_returns_error(self, client):
        """Test that missing query returns error event."""
        response = client.post('/search/rag/stream',
            json={},
            content_type='application/json'
        )
        
        events = parse_sse_response(response.data)
        
        assert len(events) == 1
        assert events[0]['type'] == 'error'
        assert 'query' in events[0]['message'].lower()
    
    def test_activity_id_in_response_header(self, client):
        """Test that X-Activity-ID is echoed in response."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_stream.return_value = iter([{'full_response': '', 'eval_count': 0}])
            
            activity_id = 'test-activity-123'
            response = client.post('/search/rag/stream',
                json={'query': 'Test'},
                content_type='application/json',
                headers={'X-Activity-ID': activity_id}
            )
            
            assert response.headers.get('X-Activity-ID') == activity_id
    
    def test_trivial_query_skips_context(self, client):
        """Test that trivial queries skip ChromaDB retrieval."""
        with patch('app.encode_texts') as mock_encode, \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_stream.return_value = iter([
                'data: {"type": "token", "content": "Hi"}\n\n',
                {'full_response': 'Hi', 'eval_count': 1}
            ])
            
            response = client.post('/search/rag/stream',
                json={'query': 'hi'},
                content_type='application/json'
            )
            
            events = parse_sse_response(response.data)
            start_event = next(e for e in events if e['type'] == 'start')
            
            # Trivial query should have top_k=0
            assert start_event['query_complexity']['top_k'] == 0
    
    def test_query_complexity_in_start_event(self, client):
        """Test that query complexity is included in start event."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag_stream') as mock_stream:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_stream.return_value = iter([
                {'full_response': 'Response', 'eval_count': 1}
            ])
            
            response = client.post('/search/rag/stream',
                json={'query': 'What is the meaning of life?'},
                content_type='application/json'
            )
            
            events = parse_sse_response(response.data)
            start_event = next(e for e in events if e['type'] == 'start')
            
            assert 'query_complexity' in start_event
            assert 'top_k' in start_event['query_complexity']
            assert 'max_tokens' in start_event['query_complexity']
            assert 'description' in start_event['query_complexity']


class TestExistingRagEndpoint:
    """Regression tests for existing /search/rag endpoint."""
    
    def test_non_streaming_endpoint_still_works(self, client):
        """Test that /search/rag still works (non-streaming)."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag') as mock_rag:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_rag.return_value = ('Test response', {'eval_count': 1})
            
            response = client.post('/search/rag',
                json={'query': 'Test'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'response' in data
            assert data['response'] == 'Test response'
    
    def test_non_streaming_returns_json(self, client):
        """Test that /search/rag returns JSON, not SSE."""
        with patch('app.encode_texts', return_value=[[0.1] * 384]), \
             patch('app.get_collection') as mock_coll, \
             patch('app.generate_with_rag') as mock_rag:
            
            mock_coll.return_value.query.return_value = {
                'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]
            }
            mock_rag.return_value = ('Response', {'eval_count': 1})
            
            response = client.post('/search/rag',
                json={'query': 'Test'},
                content_type='application/json'
            )
            
            assert 'application/json' in response.content_type
