"""
Search service for Krakenly API
Handles semantic search and query complexity analysis
"""
from typing import Tuple


def determine_query_complexity(query: str) -> Tuple[int, int]:
    """
    Auto-determine optimal top_k and max_tokens based on query complexity.
    
    Analyzes the query to decide how much context to retrieve and how long
    the response should be. This optimizes for speed on simple queries
    and thoroughness on complex ones.
    
    Args:
        query: The user's search query
        
    Returns:
        tuple: (top_k, max_tokens) - optimal settings for this query
    """
    query_lower = query.lower().strip()
    word_count = len(query.split())
    char_count = len(query)
    
    # Trivial queries - greetings, single words, etc. (no context needed)
    trivial_patterns = [
        'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye', 
        'ok', 'okay', 'yes', 'no', 'help', 'test'
    ]
    is_trivial = query_lower in trivial_patterns or (word_count == 1 and char_count < 10)
    
    if is_trivial:
        # Trivial query: minimal response, skip context retrieval
        return (0, 32)
    
    # Keywords indicating need for comprehensive response
    comprehensive_keywords = [
        'list', 'all', 'every', 'explain', 'describe', 'compare', 
        'difference', 'how many', 'what are', 'summarize', 'overview'
    ]
    
    # Keywords indicating simple/quick response
    simple_keywords = [
        'what is', 'define', 'who is', 'when', 'where', 'yes or no', 'true or false'
    ]
    
    # Check for comprehensive query patterns
    is_comprehensive = any(kw in query_lower for kw in comprehensive_keywords)
    is_simple = any(kw in query_lower for kw in simple_keywords) and word_count < 8
    
    # Determine complexity level (optimized for CPU inference ~10 tok/s)
    # Using fewer chunks (max 3) to keep context under 3000 chars
    if is_simple or (char_count < 30 and word_count < 5):
        # Simple query: quick response
        return (2, 64)
    elif is_comprehensive or char_count > 100 or word_count > 15:
        # Complex query: more context, but still limited tokens
        return (3, 128)
    else:
        # Medium query: balanced response
        return (3, 96)


def get_complexity_description(top_k: int, max_tokens: int) -> str:
    """
    Get a human-readable description of the complexity settings.
    
    Args:
        top_k: Number of context chunks to retrieve
        max_tokens: Maximum tokens for response
        
    Returns:
        str: Description of the complexity level
    """
    if top_k == 0:
        return "trivial (no context)"
    elif top_k <= 3:
        return "simple"
    elif top_k <= 5:
        return "medium"
    else:
        return "complex"