#!/usr/bin/env python3
"""
Krakenly Example: Index sample data and perform searches
"""
import requests
import json
import time

# API URL (all endpoints on port 5000)
API_URL = "http://localhost:5000"

def wait_for_services():
    """Wait for services to be ready"""
    print("Waiting for services to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✓ API service is ready")
                    print(f"  Ollama: {data.get('ollama', {}).get('running', False)}")
                    print(f"  ChromaDB: {data.get('chromadb', {}).get('running', False)}")
                    return True
        except Exception:
            pass
        time.sleep(2)
    print("✗ Services not ready after 60 seconds")
    return False

def index_data():
    """Index sample data"""
    print("\n📚 Indexing sample data...")
    
    sample_data = [
        {
            "text": "Kubernetes is an open-source container orchestration platform that automates deploying, scaling, and managing containerized applications. It was originally designed by Google and is now maintained by the Cloud Native Computing Foundation.",
            "metadata": {
                "source": "kubernetes-basics.txt",
                "type": "documentation",
                "topic": "kubernetes"
            }
        },
        {
            "text": "Docker is a platform that uses OS-level virtualization to deliver software in packages called containers. Containers are isolated from one another and bundle their own software, libraries and configuration files.",
            "metadata": {
                "source": "docker-intro.txt",
                "type": "documentation",
                "topic": "docker"
            }
        },
        {
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.",
            "metadata": {
                "source": "ml-overview.txt",
                "type": "documentation",
                "topic": "machine-learning"
            }
        },
        {
            "text": "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "metadata": {
                "source": "python-intro.txt",
                "type": "documentation",
                "topic": "programming"
            }
        }
    ]
    
    indexed = 0
    for doc in sample_data:
        response = requests.post(
            f"{API_URL}/index",
            json=doc
        )
        if response.status_code == 200:
            indexed += 1
        else:
            print(f"✗ Error indexing {doc['metadata']['source']}: {response.text}")
    
    print(f"✓ Indexed {indexed} data items")

def search_example():
    """Perform a simple search"""
    print("\n🔍 Performing semantic search...")
    
    query = "container orchestration platform"
    response = requests.post(
        f"{API_URL}/search",
        json={"query": query, "top_k": 3}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Query: '{query}'")
        print(f"Found {result['count']} results:\n")
        
        for i, doc in enumerate(result['results'], 1):
            print(f"{i}. {doc['text'][:100]}...")
            print(f"   Source: {doc['metadata'].get('source', 'unknown')}")
            print(f"   Distance: {doc.get('distance', 'N/A'):.4f}\n")
    else:
        print(f"✗ Error searching: {response.text}")

def rag_example():
    """Perform RAG-based query"""
    print("\n💬 Performing RAG query...")
    
    query = "What is Kubernetes and how does it work?"
    response = requests.post(
        f"{API_URL}/search/rag",
        json={
            "query": query,
            "top_k": 2,
            "max_tokens": 256
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Query: '{query}'")
        print(f"\nAI Response:")
        print(result['response'])
        print(f"\nSources used: {', '.join(result['sources'])}")
        print(f"Context chunks: {result['context_chunks_used']}")
    else:
        print(f"✗ Error with RAG: {response.text}")

def health_check():
    """Get service health"""
    print("\n📊 Getting service health...")
    
    response = requests.get(f"{API_URL}/health")
    
    if response.status_code == 200:
        health = response.json()
        print(f"Status: {health['status']}")
        print(f"Documents indexed: {health['documents_count']}")
        print(f"Embedding model: {health['embeddings']['model']}")
        print(f"LLM model: {health['ollama']['model']}")
    else:
        print(f"✗ Error getting health: {response.text}")

if __name__ == "__main__":
    print("=== Krakenly Example ===\n")
    
    # Wait for services
    if not wait_for_services():
        print("\n⚠ Services not ready. Make sure to run:")
        print("  ./scripts/start-docker.sh")
        exit(1)
    
    # Run examples
    index_data()
    time.sleep(2)  # Wait for indexing to complete
    
    health_check()
    search_example()
    rag_example()
    
    print("\n✅ Example completed!")
    print("\nNext steps:")
    print("  - Index your own data")
    print("  - Try different search queries")
    print("  - Experiment with RAG parameters")
