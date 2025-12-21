"""
Indexing service for Krakenly API
Handles text chunking and JSON document processing with comprehensive preprocessing
for optimal search accuracy.
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, MAX_JSON_CHUNK_SIZE


def chunk_text(text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None, document_context: Optional[str] = None) -> List[str]:
    """
    Split text into overlapping chunks for indexing.
    
    Attempts to break at natural boundaries (periods, newlines, spaces)
    rather than mid-word.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk (default from config)
        overlap: Overlap between chunks (default from config)
        document_context: Optional context to prepend to each chunk
        
    Returns:
        List of text chunks
    """
    chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
    overlap = overlap or DEFAULT_CHUNK_OVERLAP
    
    if len(text) <= chunk_size:
        if document_context:
            return [f"[{document_context}]\n{text}"]
        return [text]
    
    chunks: List[str] = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Try to break at natural boundaries
            last_period = text[start:end].rfind('. ')
            last_newline = text[start:end].rfind('\n')
            last_space = text[start:end].rfind(' ')
            break_point = max(last_period, last_newline, last_space)
            if break_point > 0:
                end = start + break_point + 1
        
        chunk_content = text[start:end].strip()
        if document_context:
            chunk_content = f"[{document_context}]\n{chunk_content}"
        chunks.append(chunk_content)
        start = end - overlap if end < len(text) else end
    
    return chunks


def preprocess_document(content: str, filename: str) -> Tuple[List[str], Dict[str, Any]]:
    """
    Comprehensive document preprocessing for optimal search.
    
    This is the main entry point for document preprocessing.
    Returns a list of enriched chunks ready for embedding.
    
    Args:
        content: Raw document content (string)
        filename: Original filename
        
    Returns:
        tuple: (chunks, metadata) where chunks is list of preprocessed text chunks
    """
    chunks: List[str] = []
    metadata: Dict[str, Any] = {
        'filename': filename,
        'preprocessing': 'enhanced'
    }
    
    # Detect document type
    is_json = filename.endswith('.json') or content.strip().startswith('{') or content.strip().startswith('[')
    
    if is_json:
        try:
            data = json.loads(content)
            chunks = preprocess_json_document(data, filename)
            metadata['type'] = 'json'
            metadata['chunking'] = 'json-aware-enhanced'
        except json.JSONDecodeError:
            # Fall back to text processing
            chunks = preprocess_text_document(content, filename)
            metadata['type'] = 'text'
            metadata['chunking'] = 'text-enhanced'
    else:
        chunks = preprocess_text_document(content, filename)
        metadata['type'] = 'text'
        metadata['chunking'] = 'text-enhanced'
    
    return chunks, metadata


def preprocess_text_document(content: str, filename: str) -> List[str]:
    """
    Preprocess a text document with enhanced chunking.
    
    Args:
        content: Text content
        filename: Document filename
        
    Returns:
        List of preprocessed chunks
    """
    chunks: List[str] = []
    
    # 1. Generate document summary as first chunk
    doc_summary = generate_text_summary(content, filename)
    chunks.append(doc_summary)
    
    # 2. Extract sections if document has headers
    sections = extract_text_sections(content)
    
    if sections:
        # Chunk by section with section context
        for section_title, section_content in sections:
            context = f"{filename} > {section_title}"
            section_chunks = chunk_text(section_content, document_context=context)
            chunks.extend(section_chunks)
    else:
        # Regular chunking with document context
        content_chunks = chunk_text(content, document_context=filename)
        chunks.extend(content_chunks)
    
    # 3. Extract and add Q&A style chunks for key information
    qa_chunks = extract_qa_chunks(content, filename)
    chunks.extend(qa_chunks)
    
    return chunks


def generate_text_summary(content: str, filename: str) -> str:
    """
    Generate a summary chunk for a text document.
    
    Args:
        content: Document content
        filename: Document filename
        
    Returns:
        Summary string
    """
    lines = content.split('\n')
    non_empty_lines = [l.strip() for l in lines if l.strip()]
    
    # Get first few meaningful lines
    preview_lines = non_empty_lines[:5]
    preview = ' '.join(preview_lines)[:300]
    
    word_count = len(content.split())
    line_count = len(non_empty_lines)
    
    summary = f"""Document: {filename}
Summary: This document contains {word_count} words across {line_count} lines.
Preview: {preview}{'...' if len(preview) >= 300 else ''}
"""
    return summary


def extract_text_sections(content: str) -> List[Tuple[str, str]]:
    """
    Extract sections from text based on headers.
    
    Looks for Markdown-style headers (# Header) or
    ALL CAPS lines as section dividers.
    
    Args:
        content: Text content
        
    Returns:
        List of (section_title, section_content) tuples
    """
    sections: List[Tuple[str, str]] = []
    
    # Try Markdown headers
    md_pattern = r'^(#{1,3})\s+(.+)$'
    lines = content.split('\n')
    
    current_section: Optional[str] = None
    current_content: List[str] = []
    
    for line in lines:
        md_match = re.match(md_pattern, line)
        # Also check for ALL CAPS headers (at least 3 words)
        is_caps_header = (
            line.isupper() and 
            len(line.split()) >= 2 and 
            len(line) < 100
        )
        
        if md_match or is_caps_header:
            # Save previous section
            if current_section and current_content:
                sections.append((current_section, '\n'.join(current_content)))
            
            current_section = md_match.group(2) if md_match else line.strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Don't forget last section
    if current_section and current_content:
        sections.append((current_section, '\n'.join(current_content)))
    
    return sections


def extract_qa_chunks(content: str, filename: str) -> List[str]:
    """
    Extract Q&A style chunks from content.
    
    Looks for patterns like:
    - "X is Y" -> "What is X? X is Y"
    - Definitions and key facts
    
    Args:
        content: Document content
        filename: Document filename
        
    Returns:
        List of Q&A formatted chunks
    """
    qa_chunks: List[str] = []
    
    # Pattern: "X is a/an/the Y" - definition pattern
    definition_pattern = r'([A-Z][^.]*?)\s+is\s+(a|an|the)\s+([^.]+\.)'
    
    for match in re.finditer(definition_pattern, content):
        subject = match.group(1).strip()
        definition = match.group(0).strip()
        
        if len(subject) > 3 and len(definition) > 20:
            qa = f"[{filename}] What is {subject}?\nAnswer: {definition}"
            qa_chunks.append(qa)
    
    return qa_chunks[:10]  # Limit to avoid too many small chunks


def preprocess_json_document(data: Any, filename: str) -> List[str]:
    """
    Comprehensive preprocessing for JSON documents.
    
    Creates multiple types of chunks:
    1. Document overview/summary
    2. Schema description
    3. Hierarchical path chunks
    4. Entity-focused chunks
    5. Relationship chunks
    6. Searchable key-value pairs
    
    Args:
        data: Parsed JSON data
        filename: Document filename
        
    Returns:
        List of preprocessed chunks
    """
    chunks: List[str] = []
    
    # 1. Document Overview
    overview = generate_json_overview(data, filename)
    chunks.append(overview)
    
    # 2. Schema Description
    schema = generate_json_schema_description(data, filename)
    chunks.append(schema)
    
    # 3. Extract all entities with full path context
    entity_chunks = extract_json_entities(data, filename)
    chunks.extend(entity_chunks)
    
    # 4. Generate relationship chunks
    relationship_chunks = extract_json_relationships(data, filename)
    chunks.extend(relationship_chunks)
    
    # 5. Generate searchable index of all values
    index_chunks = generate_json_index(data, filename)
    chunks.extend(index_chunks)
    
    # 6. Q&A style chunks for common queries
    qa_chunks = generate_json_qa_chunks(data, filename)
    chunks.extend(qa_chunks)
    
    return chunks


def generate_json_overview(data: Any, filename: str) -> str:
    """
    Generate a high-level overview of the JSON document.
    """
    lines = [f"Document: {filename}", "Type: JSON Document", ""]
    
    if isinstance(data, dict):
        lines.append(f"Top-level keys: {', '.join(list(data.keys())[:10])}")
        lines.append(f"Total top-level properties: {len(data)}")
        
        # Count nested items
        total_items = count_json_items(data)
        lines.append(f"Total nested items: {total_items}")
        
        # Identify main content arrays
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    lines.append(f"  - {key}: array of {len(value)} objects")
                else:
                    lines.append(f"  - {key}: array of {len(value)} values")
                    
    elif isinstance(data, list):
        lines.append(f"Root: Array with {len(data)} items")
        if data and isinstance(data[0], dict):
            lines.append(f"Item fields: {', '.join(list(data[0].keys())[:10])}")
    
    return '\n'.join(lines)


def count_json_items(data: Any, max_depth: int = 10, current_depth: int = 0) -> int:
    """Recursively count all items in JSON structure."""
    if current_depth > max_depth:
        return 0
    
    count = 0
    if isinstance(data, dict):
        count += len(data)
        for value in data.values():
            count += count_json_items(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        count += len(data)
        for item in data:
            count += count_json_items(item, max_depth, current_depth + 1)
    return count


def generate_json_schema_description(data: Any, filename: str) -> str:
    """
    Generate a schema-like description of the JSON structure.
    """
    lines = [f"Schema for {filename}:", ""]
    
    def describe_structure(obj: Any, indent: int = 0, path: str = "") -> List[str]:
        result = []
        prefix = "  " * indent
        
        if isinstance(obj, dict):
            for key, value in list(obj.items())[:20]:  # Limit keys
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    result.append(f"{prefix}{key}: object")
                    if indent < 2:  # Limit depth
                        result.extend(describe_structure(value, indent + 1, current_path))
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        result.append(f"{prefix}{key}: array of objects")
                        if indent < 2:
                            result.extend(describe_structure(value[0], indent + 1, current_path))
                    else:
                        result.append(f"{prefix}{key}: array")
                else:
                    val_type = type(value).__name__
                    result.append(f"{prefix}{key}: {val_type}")
        
        return result
    
    lines.extend(describe_structure(data))
    return '\n'.join(lines)


def extract_json_entities(data: Any, filename: str, path: str = "", max_chunk_size: Optional[int] = None) -> List[str]:
    """
    Extract entities from JSON with full hierarchical context.
    
    Each entity chunk includes:
    - Full path from root
    - Parent context
    - All properties
    """
    max_chunk_size = max_chunk_size or MAX_JSON_CHUNK_SIZE
    chunks: List[str] = []
    
    def extract_recursive(obj: Any, current_path: str, parent_context: str = ""):
        if isinstance(obj, dict):
            # Check if this looks like an entity (has name/id/type)
            is_entity = any(k in obj for k in ['name', 'id', 'type', 'title', 'key'])
            
            if is_entity:
                # Create entity chunk with full context
                entity_name = obj.get('name') or obj.get('id') or obj.get('title') or obj.get('key') or 'unnamed'
                
                chunk_lines = [
                    f"[{filename}]",
                    f"Path: {current_path}",
                ]
                
                if parent_context:
                    chunk_lines.append(f"Context: {parent_context}")
                
                chunk_lines.append(f"\nEntity: {entity_name}")
                chunk_lines.append("Properties:")
                
                for key, value in obj.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        chunk_lines.append(f"  {key}: {value}")
                    elif isinstance(value, list):
                        if value and not isinstance(value[0], dict):
                            chunk_lines.append(f"  {key}: {', '.join(str(v) for v in value[:10])}")
                        else:
                            chunk_lines.append(f"  {key}: [{len(value)} items]")
                    elif isinstance(value, dict):
                        chunk_lines.append(f"  {key}: [object]")
                
                chunk_text = '\n'.join(chunk_lines)
                if len(chunk_text) <= max_chunk_size:
                    chunks.append(chunk_text)
            
            # Recurse into nested structures
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Build parent context
                entity_name = obj.get('name') or obj.get('id') or ''
                new_context = f"{parent_context} > {entity_name}" if entity_name else parent_context
                
                if isinstance(value, (dict, list)):
                    extract_recursive(value, new_path, new_context.strip(' > '))
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                item_path = f"{current_path}[{i}]"
                if isinstance(item, dict):
                    # Use item's name/id in path if available
                    item_name = item.get('name') or item.get('id')
                    if item_name:
                        item_path = f"{current_path}: {item_name}"
                
                extract_recursive(item, item_path, parent_context)
    
    extract_recursive(data, "", "")
    return chunks


def extract_json_relationships(data: Any, filename: str) -> List[str]:
    """
    Extract relationships between entities in the JSON.
    """
    chunks: List[str] = []
    relationships: List[str] = []
    
    def find_relationships(obj: Any, path: str = "", parent_name: Optional[str] = None):
        if isinstance(obj, dict):
            current_name = obj.get('name') or obj.get('id')
            
            # Parent-child relationship
            if parent_name and current_name:
                relationships.append(f"{parent_name} contains {current_name}")
            
            # Look for reference fields
            for key, value in obj.items():
                if isinstance(value, str) and ('id' in key.lower() or 'ref' in key.lower()):
                    if current_name:
                        relationships.append(f"{current_name} references {value} (via {key})")
            
            # Recurse
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    find_relationships(value, f"{path}.{key}", current_name)
                    
        elif isinstance(obj, list):
            for item in obj:
                find_relationships(item, path, parent_name)
    
    find_relationships(data)
    
    # Create relationship chunks
    if relationships:
        # Group into chunks of 20 relationships
        for i in range(0, len(relationships), 20):
            batch = relationships[i:i+20]
            chunk = f"[{filename}] Relationships:\n" + '\n'.join(f"  - {r}" for r in batch)
            chunks.append(chunk)
    
    return chunks


def generate_json_index(data: Any, filename: str) -> List[str]:
    """
    Generate a searchable index of all key-value pairs.
    """
    chunks: List[str] = []
    index_entries: List[str] = []
    
    def build_index(obj: Any, path: str = ""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                if isinstance(value, (str, int, float, bool)) or value is None:
                    index_entries.append(f"{new_path} = {value}")
                elif isinstance(value, list) and value and not isinstance(value[0], dict):
                    index_entries.append(f"{new_path} = [{', '.join(str(v) for v in value[:5])}{'...' if len(value) > 5 else ''}]")
                else:
                    build_index(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    # Use name/id in path
                    item_name = item.get('name') or item.get('id') or str(i)
                    build_index(item, f"{path}[{item_name}]")
                else:
                    index_entries.append(f"{path}[{i}] = {item}")
    
    build_index(data)
    
    # Create index chunks (group by path prefix)
    if index_entries:
        # Group into chunks of 30 entries
        for i in range(0, len(index_entries), 30):
            batch = index_entries[i:i+30]
            chunk = f"[{filename}] Index:\n" + '\n'.join(batch)
            chunks.append(chunk)
    
    return chunks


def generate_json_qa_chunks(data: Any, filename: str) -> List[str]:
    """
    Generate Q&A style chunks for common query patterns.
    """
    chunks: List[str] = []
    
    # Find all named entities
    entities: List[Dict[str, Any]] = []
    
    def collect_entities(obj: Any, path: str = ""):
        if isinstance(obj, dict):
            name = obj.get('name') or obj.get('id') or obj.get('title')
            if name:
                entities.append({
                    'name': name,
                    'path': path,
                    'type': obj.get('type') or obj.get('kind') or 'entity',
                    'properties': [k for k in obj.keys() if not isinstance(obj[k], (dict, list))]
                })
            
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    collect_entities(value, f"{path}.{key}" if path else key)
                    
        elif isinstance(obj, list):
            for item in obj:
                collect_entities(item, path)
    
    collect_entities(data)
    
    # Generate "What is X?" chunks
    for entity in entities[:50]:  # Limit
        qa = f"""[{filename}] What is {entity['name']}?
Answer: {entity['name']} is a {entity['type']} located at {entity['path']}.
Properties: {', '.join(entity['properties'][:10])}"""