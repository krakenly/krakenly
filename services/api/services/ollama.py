"""
Ollama service for Krakenly API
Handles interaction with Ollama LLM service
"""
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from config import (
    OLLAMA_HOST, 
    MODEL_NAME, 
    OLLAMA_TIMEOUT,
    OLLAMA_PULL_TIMEOUT,
    WARMUP_MAX_RETRIES,
    WARMUP_RETRY_DELAY
)


def warmup_ollama_model() -> bool:
    """
    Warm up the Ollama model by sending a test request to load it into memory.
    
    This is called at startup to ensure the model is ready for the first request,
    avoiding the initial cold-start latency.
    
    Returns:
        bool: True if model was successfully warmed up, False otherwise
    """
    print(f"Warming up Ollama model: {MODEL_NAME}")
    
    for attempt in range(WARMUP_MAX_RETRIES):
        try:
            # First check if Ollama is responding
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if resp.status_code != 200:
                raise Exception("Ollama not ready")
            
            # Check if model is available
            models = resp.json().get('models', [])
            model_available = any(m['name'] == MODEL_NAME for m in models)
            
            if not model_available:
                print(f"  Model {MODEL_NAME} not found, pulling...")
                pull_resp = requests.post(
                    f"{OLLAMA_HOST}/api/pull",
                    json={"name": MODEL_NAME, "stream": False},
                    timeout=OLLAMA_PULL_TIMEOUT
                )
                if pull_resp.status_code != 200:
                    print(f"  Warning: Could not pull model: {pull_resp.text}")
            
            # Send a warmup request to load model into memory
            print(f"  Loading model into memory...")
            t0 = time.time()
            warmup_resp = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": "Hi",
                    "stream": False,
                    "options": {"num_predict": 1}  # Generate just 1 token
                },
                timeout=120
            )
            
            if warmup_resp.status_code == 200:
                elapsed = time.time() - t0
                print(f"  Model {MODEL_NAME} loaded and ready! (warmup took {elapsed:.1f}s)")
                return True
            else:
                print(f"  Warmup failed: {warmup_resp.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"  Waiting for Ollama to start... (attempt {attempt + 1}/{WARMUP_MAX_RETRIES})")
            time.sleep(WARMUP_RETRY_DELAY)
        except Exception as e:
            print(f"  Warmup attempt {attempt + 1} failed: {e}")
            time.sleep(WARMUP_RETRY_DELAY)
    
    print(f"Warning: Could not warm up Ollama model after {WARMUP_MAX_RETRIES} attempts")
    return False


def generate_text(prompt: str, context: str = '', max_tokens: int = 512, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Generate text using Ollama.
    
    Args:
        prompt: The prompt to generate from
        context: Optional context to prepend
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        dict: Response with 'response', 'model', and 'done' fields
    """
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens, 
                "temperature": temperature, 
                "top_p": 0.9
            }
        },
        timeout=OLLAMA_TIMEOUT
    )
    
    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")
    
    result = response.json()
    return {
        'response': result.get('response', ''),
        'model': MODEL_NAME,
        'done': result.get('done', False)
    }


def generate_with_rag(prompt: str, context: str = '', max_tokens: int = 512, temperature: float = 0.7) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Generate text with RAG context.
    Returns raw response data including timing info.
    
    Args:
        prompt: The user query
        context: Retrieved context from search
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        tuple: (response_text, raw_response_data)
    """
    # Import here to avoid circular import
    from config import MAX_CONTEXT_CHARS
    
    # Truncate context if too large for CPU inference
    if context and len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n[...truncated for performance...]"
    
    if context:
        full_prompt = f"Based on the following information:\n\n{context}\n\nPlease answer: {prompt}"
    else:
        full_prompt = prompt
    
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens, 
                "temperature": temperature
            }
        },
        timeout=OLLAMA_TIMEOUT
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('response', ''), data
    else:
        return f"Error: {response.status_code}", None


def chat_with_history(messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> Dict[str, str]:
    """
    Chat with message history using Ollama chat endpoint.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        dict: Response with 'response' and 'model' fields
    """
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens, 
                "temperature": temperature
            }
        },
        timeout=OLLAMA_TIMEOUT
    )
    
    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")
    
    result = response.json()
    return {
        'response': result.get('message', {}).get('content', ''),
        'model': MODEL_NAME
    }


def pull_model(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Pull a model into Ollama.
    
    Args:
        model_name: Name of model to pull, defaults to configured MODEL_NAME
        
    Returns:
        dict: Status response
    """
    model = model_name or MODEL_NAME
    
    response = requests.post(
        f"{OLLAMA_HOST}/api/pull",
        json={"name": model, "stream": False},
        timeout=OLLAMA_PULL_TIMEOUT
    )
    
    return {
        'status': 'success' if response.status_code == 200 else 'error',
        'model': model,
        'response': response.json() if response.status_code == 200 else response.text
    }


def list_models() -> Dict[str, Any]:
    """
    List available models in Ollama.
    
    Returns:
        dict: Models response from Ollama
    """
    response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
    if response.status_code == 200:
        return response.json()
    raise Exception("Could not fetch models")


def check_health() -> Dict[str, Any]:
    """
    Check Ollama health and model availability.
    
    Returns:
        dict: Health status with 'running' and 'model_loaded' fields
    """
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            model_ready = any(m['name'] == MODEL_NAME for m in models)
            return {
                'running': True,
                'model_loaded': model_ready,
                'model': MODEL_NAME
            }
    except Exception:
        pass
    
    return {
        'running': False,
        'model_loaded': False,
        'model': MODEL_NAME
    }
    