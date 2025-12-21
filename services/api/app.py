"""
Krakenly API Service
Unified REST API for document indexing, search, and AI generation
Uses official Ollama and ChromaDB services

This is the main entry point that defines routes and orchestrates services.
"""
import uuid
import json
import time
from datetime import datetime
from typing import Union, Tuple
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# Import configuration
from config import MODEL_NAME, EMBEDDING_MODEL

# Import services
from services.embedding import init_embedder, encode_texts
from services.ollama import (
    warmup_ollama_model, 
    generate_text, 
    pull_model,
    list_models,
    check_health as check_ollama_health,
    generate_with_rag,
    generate_with_rag_stream
)
from services.chromadb import init_chromadb, get_collection, check_health as check_chromadb_health
from services.indexing import chunk_text, chunk_json_document, preprocess_document
from services.search import determine_query_complexity, get_complexity_description

# Import utilities
from utils.logging import setup_logging, get_logger, create_request_logger
from utils.metadata import load_metadata, add_source, remove_source, list_sources

# Setup logging
setup_logging()
logger = get_logger()

# Create Flask app
app = Flask(__name__)
CORS(app, expose_headers=['X-Activity-ID'])

# Add request/response logging middleware
create_request_logger(app)


def init_services() -> None:
    """Initialize all services: embeddings, ChromaDB, Ollama, and metadata"""
    init_embedder()
    init_chromadb()
    warmup_ollama_model()
    load_metadata()


# Initialize at module load
try:
    init_services()
except Exception as e:
    print(f"Warning: Could not initialize services at startup: {e}")


# ============== Health & Status ==============

@app.route('/health', methods=['GET'])
def health() -> Response:
    """Health check endpoint"""
    ollama_status = check_ollama_health()
    chromadb_status = check_chromadb_health()
    collection = get_collection()
    
    is_healthy = ollama_status['running'] and chromadb_status['running']
    
    return jsonify({
        'status': 'healthy' if is_healthy else 'degraded',
        'ollama': ollama_status,
        'chromadb': chromadb_status,
        'embeddings': {'model': EMBEDDING_MODEL},
        'documents_count': collection.count() if collection else 0
    })


# ============== Document Indexing ==============

@app.route('/index', methods=['POST'])
def index_document() -> Union[Response, Tuple[Response, int]]:
    """Index a document with chunking and embedding"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text in request'}), 400
        
        text = data['text']
        metadata = data.get('metadata', {})
        chunk_size = data.get('chunk_size', 500)
        chunk_overlap = data.get('chunk_overlap', 50)
        
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        embeddings = encode_texts(chunks)
        
        doc_id = metadata.get('source', str(uuid.uuid4()))
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        metadatas = []
        for i in range(len(chunks)):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            chunk_metadata['indexed_at'] = datetime.utcnow().isoformat()
            metadatas.append(chunk_metadata)
        
        collection = get_collection()
        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        
        # Track source metadata
        add_source(
            doc_id, 
            len(chunks), 
            len(text),
            {k: v for k, v in metadata.items() if k != 'source'}
        )
        
        return jsonify({
            'status': 'success',
            'document_id': doc_id,
            'chunks_indexed': len(chunks),
            'total_documents': collection.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/index/batch', methods=['POST'])
def index_batch() -> Union[Response, Tuple[Response, int]]:
    """Index multiple documents"""
    try:
        data = request.get_json()
        if not data or 'documents' not in data:
            return jsonify({'error': 'Missing documents in request'}), 400
        
        documents = data['documents']
        chunk_size = data.get('chunk_size', 500)
        chunk_overlap = data.get('chunk_overlap', 50)
        
        total_chunks = 0
        indexed_docs = []
        collection = get_collection()
        
        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            if not text:
                continue
            
            chunks = chunk_text(text, chunk_size, chunk_overlap)
            embeddings = encode_texts(chunks)
            
            doc_id = metadata.get('source', str(uuid.uuid4()))
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            
            metadatas = [
                {
                    **metadata, 
                    'chunk_index': i, 
                    'total_chunks': len(chunks), 
                    'indexed_at': datetime.utcnow().isoformat()
                } 
                for i in range(len(chunks))
            ]
            
            collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
            total_chunks += len(chunks)
            indexed_docs.append(doc_id)
            
            # Track source metadata
            add_source(
                doc_id,
                len(chunks),
                len(text),
                {k: v for k, v in metadata.items() if k != 'source'}
            )
        
        return jsonify({
            'status': 'success',
            'documents_indexed': len(indexed_docs),
            'total_chunks': total_chunks,
            'document_ids': indexed_docs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/index/upload', methods=['POST'])
def upload_file() -> Union[Response, Tuple[Response, int]]:
    """Upload and index a file with comprehensive preprocessing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        content = file.read().decode('utf-8', errors='ignore')
        filename = file.filename
        
        # Get optional metadata from form
        metadata = {'source': filename}
        if request.form.get('type'):
            metadata['type'] = request.form.get('type')
        
        # Use enhanced preprocessing
        start_time = time.time()
        chunks, preprocess_metadata = preprocess_document(content, filename)
        preprocess_time = time.time() - start_time
        
        # Merge preprocessing metadata
        metadata.update(preprocess_metadata)
        
        embeddings = encode_texts(chunks)
        
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = []
        for i in range(len(chunks)):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            chunk_metadata['indexed_at'] = datetime.utcnow().isoformat()
            metadatas.append(chunk_metadata)
        
        collection = get_collection()
        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        
        # Track source metadata
        add_source(
            filename,
            len(chunks),
            len(content),
            {k: v for k, v in metadata.items() if k != 'source'}
        )
        
        logger.info(f"Preprocessed {filename}: {len(chunks)} chunks in {preprocess_time:.2f}s")
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'chunks_indexed': len(chunks),
            'size_bytes': len(content),
            'preprocess_time_sec': round(preprocess_time, 2),
            'chunking_method': metadata.get('chunking', 'unknown'),
            'total_documents': collection.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/sources', methods=['GET'])
def get_sources() -> Union[Response, Tuple[Response, int]]:
    """List all indexed sources with metadata"""
    try:
        sources = list_sources()
        collection = get_collection()
        
        return jsonify({
            'sources': sources,
            'total_sources': len(sources),
            'total_chunks': collection.count() if collection else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/sources/<path:source_id>', methods=['DELETE'])
def delete_source(source_id: str) -> Union[Response, Tuple[Response, int]]:
    """Delete all chunks from a specific source"""
    try:
        collection = get_collection()
        
        # Get all chunk IDs for this source
        results = collection.get(where={'source': source_id}, include=['metadatas'])
        
        if not results or not results['ids']:
            return jsonify({'error': 'Source not found'}), 404
        
        # Delete from ChromaDB
        collection.delete(ids=results['ids'])
        
        # Remove from metadata
        remove_source(source_id)
        
        return jsonify({
            'status': 'success',
            'source': source_id,
            'chunks_deleted': len(results['ids']),
            'total_documents': collection.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats() -> Response:
    """Get indexing statistics"""
    collection = get_collection()
    sources = list_sources()
    
    return jsonify({
        'total_chunks': collection.count() if collection else 0,
        'total_sources': len(sources),
        'embedding_model': EMBEDDING_MODEL,
        'embedding_dimension': 384
    })


# ============== Search ==============

@app.route('/search', methods=['POST'])
def search() -> Union[Response, Tuple[Response, int]]:
    """Semantic search across indexed documents"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query in request'}), 400
        
        query = data['query']
        top_k = data.get('top_k', 5)
        metadata_filter = data.get('filter', None)
        
        query_embedding = encode_texts([query])[0]
        
        search_kwargs = {'query_embeddings': [query_embedding], 'n_results': top_k}
        if metadata_filter:
            search_kwargs['where'] = metadata_filter
        
        collection = get_collection()
        results = collection.query(**search_kwargs)
        
        formatted_results = []
        if results and results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return jsonify({
            'query': query, 
            'results': formatted_results, 
            'count': len(formatted_results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/search/rag', methods=['POST'])
def search_with_rag() -> Union[Response, Tuple[Response, int]]:
    """RAG: Search + AI generation"""
    try:
        timings = {}
        t0 = time.time()
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query in request'}), 400
        
        query = data['query']
        
        # Auto-determine optimal settings based on query complexity
        auto_top_k, auto_max_tokens = determine_query_complexity(query)
        
        # Use auto values unless explicitly overridden
        top_k = data.get('top_k') or auto_top_k
        max_tokens = data.get('max_tokens') or auto_max_tokens
        temperature = data.get('temperature', 0.7)
        
        timings['auto_top_k'] = auto_top_k
        timings['auto_max_tokens'] = auto_max_tokens
        timings['used_top_k'] = top_k
        timings['used_max_tokens'] = max_tokens
        
        context_parts = []
        sources = []
        context = ""
        
        # Skip context retrieval for trivial queries (top_k=0)
        if top_k > 0:
            # Search for context
            t1 = time.time()
            query_embedding = encode_texts([query])[0]
            timings['embedding_ms'] = round((time.time() - t1) * 1000, 2)
            
            t2 = time.time()
            collection = get_collection()
            results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
            timings['chromadb_ms'] = round((time.time() - t2) * 1000, 2)
            
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    context_parts.append(results['documents'][0][i])
                    if results['metadatas'] and results['metadatas'][0]:
                        source = results['metadatas'][0][i].get('source', 'Unknown')
                        if source not in sources:
                            sources.append(source)
            
            context = "\n\n".join(context_parts)
        else:
            timings['embedding_ms'] = 0
            timings['chromadb_ms'] = 0
            timings['skipped_context'] = True
        
        timings['context_chars'] = len(context)
        
        # Generate with AI
        t3 = time.time()
        try:
            response_text, ollama_data = generate_with_rag(
                query, 
                context, 
                max_tokens, 
                temperature
            )
            timings['ollama_ms'] = round((time.time() - t3) * 1000, 2)
            
            if ollama_data:
                timings['tokens_generated'] = ollama_data.get('eval_count', 0)
                timings['tokens_per_sec'] = round(
                    ollama_data.get('eval_count', 0) / ((time.time() - t3) or 1), 1
                )
        except Exception as e:
            timings['ollama_ms'] = round((time.time() - t3) * 1000, 2)
            response_text = f"AI service error: {str(e)}"
        
        timings['total_ms'] = round((time.time() - t0) * 1000, 2)
        
        # Log detailed timing breakdown
        logger.info(f"RAG TIMING: {json.dumps(timings)}")
        
        return jsonify({
            'query': query,
            'response': response_text,
            'sources': sources,
            'context_chunks_used': len(context_parts),
            'timings': timings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/search/rag/stream', methods=['POST'])
def search_with_rag_stream() -> Response:
    """RAG with streaming response via Server-Sent Events"""
    
    # Extract request data BEFORE creating generator (outside generator context)
    data = request.get_json()
    activity_id = request.headers.get('X-Activity-ID', str(uuid.uuid4()))
    
    def generate(data, activity_id):
        """Generator for SSE stream"""
        timings = {}
        t0 = time.time()
        
        # Validate request data
        if not data or 'query' not in data:
            yield f'data: {json.dumps({"type": "error", "message": "Missing query", "code": "bad_request"})}\n\n'
            return
        
        query = data['query']
        
        # Auto-determine settings
        auto_top_k, auto_max_tokens = determine_query_complexity(query)
        top_k = data.get('top_k') or auto_top_k
        max_tokens = data.get('max_tokens') or auto_max_tokens
        temperature = data.get('temperature', 0.7)
        
        # Get context from ChromaDB
        context_parts = []
        sources = []
        context = ""
        
        if top_k > 0:
            t1 = time.time()
            query_embedding = encode_texts([query])[0]
            timings['embedding_ms'] = round((time.time() - t1) * 1000, 2)
            
            t2 = time.time()
            collection = get_collection()
            results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
            timings['chromadb_ms'] = round((time.time() - t2) * 1000, 2)
            
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    context_parts.append(results['documents'][0][i])
                    if results['metadatas'] and results['metadatas'][0]:
                        source = results['metadatas'][0][i].get('source', 'Unknown')
                        if source not in sources:
                            sources.append(source)
            
            context = "\n\n".join(context_parts)
        else:
            timings['embedding_ms'] = 0
            timings['chromadb_ms'] = 0
        
        timings['context_chars'] = len(context)
        
        # Send start event
        start_event = {
            "type": "start",
            "activity_id": activity_id,
            "sources": sources,
            "query_complexity": {
                "top_k": top_k,
                "max_tokens": max_tokens,
                "description": get_complexity_description(top_k, max_tokens)
            }
        }
        yield f'data: {json.dumps(start_event)}\n\n'
        
        # Stream tokens from Ollama
        t3 = time.time()
        full_response = ""
        ollama_stats = None
        
        try:
            for chunk in generate_with_rag_stream(query, context, max_tokens, temperature):
                if isinstance(chunk, dict):
                    # Final stats returned
                    ollama_stats = chunk
                    full_response = chunk.get('full_response', '')
                else:
                    # SSE data line - yield it
                    yield chunk
                    # Also track full response for done event
                    try:
                        event_data = json.loads(chunk.replace('data: ', '').strip())
                        if event_data.get('type') == 'token':
                            full_response += event_data.get('content', '')
                    except:
                        pass
                        
        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "message": str(e), "code": "stream_error"})}\n\n'
            return
        
        timings['ollama_ms'] = round((time.time() - t3) * 1000, 2)
        timings['total_ms'] = round((time.time() - t0) * 1000, 2)
        
        if ollama_stats:
            timings['tokens_generated'] = ollama_stats.get('eval_count', 0)
            eval_duration_sec = ollama_stats.get('eval_duration', 0) / 1e9  # nanoseconds to seconds
            if eval_duration_sec > 0:
                timings['tokens_per_sec'] = round(ollama_stats.get('eval_count', 0) / eval_duration_sec, 1)
        
        # Send done event
        done_event = {
            "type": "done",
            "full_response": full_response,
            "timings": timings
        }
        yield f'data: {json.dumps(done_event)}\n\n'
        
        logger.info(f"STREAM TIMING: {json.dumps(timings)}")
    
    # Return streaming response
    return Response(
        generate(data, activity_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'X-Activity-ID': activity_id
        }
    )


@app.route('/list', methods=['GET'])
def list_documents() -> Union[Response, Tuple[Response, int]]:
    """List indexed documents"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        collection = get_collection()
        results = collection.get(limit=limit, offset=offset, include=['metadatas', 'documents'])
        
        documents = []
        if results and results['ids']:
            for i in range(len(results['ids'])):
                documents.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i] if results['documents'] else '',
                    'metadata': results['metadatas'][i] if results['metadatas'] else {}
                })
        
        return jsonify({
            'documents': documents,
            'count': len(documents),
            'total': collection.count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== AI Generation ==============

@app.route('/generate', methods=['POST'])
def generate() -> Union[Response, Tuple[Response, int]]:
    """Generate text using Ollama"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request'}), 400
        
        prompt = data['prompt']
        context = data.get('context', '')
        max_tokens = data.get('max_tokens', 512)
        temperature = data.get('temperature', 0.7)
        
        result = generate_text(prompt, context, max_tokens, temperature)
        return jsonify(result)
        
    except Exception as e:
        if 'timeout' in str(e).lower():
            return jsonify({'error': 'Request timeout'}), 504
        return jsonify({'error': str(e)}), 500


# Note: /chat endpoint removed - all conversations use /search/rag 
# to ensure responses are grounded in the user's indexed documents.
# This is by design for Krakenly.


# ============== Model Management ==============

@app.route('/models/pull', methods=['POST'])
def pull_model_endpoint() -> Union[Response, Tuple[Response, int]]:
    """Pull a model into Ollama"""
    try:
        data = request.get_json()
        model = data.get('model', MODEL_NAME)
        
        result = pull_model(model)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/models', methods=['GET'])
def list_models_endpoint() -> Union[Response, Tuple[Response, int]]:
    """List available models in Ollama"""
    try:
        result = list_models()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)