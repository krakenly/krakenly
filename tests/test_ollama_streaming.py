"""
Unit tests for Ollama streaming service.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))


class TestGenerateWithRagStream:
    """Tests for generate_with_rag_stream function."""
    
    def test_yields_tokens_in_sse_format(self, mock_ollama_stream_response):
        """Test that tokens are yielded in correct SSE format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = mock_ollama_stream_response
        
        with patch('services.ollama.requests.post', return_value=mock_response):
            from services.ollama import generate_with_rag_stream
            
            events = list(generate_with_rag_stream("What is the answer?", "Context here"))
            
            # Filter out the final dict (stats)
            sse_events = [e for e in events if isinstance(e, str)]
            
            # Should have token events (4 tokens before done)
            assert len(sse_events) >= 4
            
            # Each should be SSE formatted
            for event in sse_events:
                assert event.startswith('data: ')
                assert event.endswith('\n\n')
                
                # Should be valid JSON
                json_str = event.replace('data: ', '').strip()
                parsed = json.loads(json_str)
                assert parsed['type'] == 'token'
                assert 'content' in parsed
    
    def test_returns_stats_on_completion(self, mock_ollama_stream_response):
        """Test that final stats are returned when stream completes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = mock_ollama_stream_response
        
        with patch('services.ollama.requests.post', return_value=mock_response):
            from services.ollama import generate_with_rag_stream
            
            events = list(generate_with_rag_stream("Test query"))
            
            # Last item should be stats dict
            stats = events[-1]
            assert isinstance(stats, dict)
            assert 'full_response' in stats
            assert stats['full_response'] == 'The answer is 42.'
            assert stats['eval_count'] == 5
    
    def test_handles_connection_error(self):
        """Test graceful handling of connection errors."""
        import requests
        
        with patch('services.ollama.requests.post', side_effect=requests.exceptions.ConnectionError()):
            from services.ollama import generate_with_rag_stream
            
            events = list(generate_with_rag_stream("Test query"))
            
            assert len(events) == 1
            event = json.loads(events[0].replace('data: ', '').strip())
            assert event['type'] == 'error'
            assert event['code'] == 'ollama_connection'
    
    def test_handles_timeout(self):
        """Test graceful handling of timeout."""
        import requests
        
        with patch('services.ollama.requests.post', side_effect=requests.exceptions.Timeout()):
            from services.ollama import generate_with_rag_stream
            
            events = list(generate_with_rag_stream("Test query"))
            
            assert len(events) == 1
            event = json.loads(events[0].replace('data: ', '').strip())
            assert event['type'] == 'error'
            assert event['code'] == 'timeout'
    
    def test_handles_ollama_error_status(self):
        """Test handling of non-200 status from Ollama."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch('services.ollama.requests.post', return_value=mock_response):
            from services.ollama import generate_with_rag_stream
            
            events = list(generate_with_rag_stream("Test query"))
            
            assert len(events) == 1
            event = json.loads(events[0].replace('data: ', '').strip())
            assert event['type'] == 'error'
            assert '500' in event['message']
    
    def test_context_included_in_prompt(self):
        """Test that context is properly included in prompt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"response":"Ok","done":true,"eval_count":1}'
        ]
        
        with patch('services.ollama.requests.post', return_value=mock_response) as mock_post:
            from services.ollama import generate_with_rag_stream
            
            context = "Some important context"
            list(generate_with_rag_stream("Query", context))
            
            call_args = mock_post.call_args
            prompt = call_args[1]['json']['prompt']
            
            assert 'Based on the following information' in prompt
            assert context in prompt
            assert 'Query' in prompt
    
    def test_empty_context_no_prefix(self):
        """Test that empty context doesn't add prefix."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"response":"Hello","done":true,"eval_count":1}'
        ]
        
        with patch('services.ollama.requests.post', return_value=mock_response) as mock_post:
            from services.ollama import generate_with_rag_stream
            
            list(generate_with_rag_stream("Hello", ""))
            
            prompt = mock_post.call_args[1]['json']['prompt']
            assert 'Based on the following' not in prompt
            assert prompt == 'Hello'
    
    def test_stream_option_enabled(self):
        """Test that stream option is set to True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"response":"Test","done":true,"eval_count":1}'
        ]
        
        with patch('services.ollama.requests.post', return_value=mock_response) as mock_post:
            from services.ollama import generate_with_rag_stream
            
            list(generate_with_rag_stream("Test"))
            
            call_args = mock_post.call_args
            assert call_args[1]['json']['stream'] is True
            assert call_args[1]['stream'] is True
