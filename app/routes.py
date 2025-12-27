# -*- coding: utf-8 -*-
"""Flask routes for SINEMA Chatbot API - Database Version"""
import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

from .config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, MODEL_DIR, BASE_DIR,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_NEW_TOKENS, TEMPERATURE, TOP_P, DEVICE, SYSTEM_PROMPT
)
from .rag import RAGRetriever
from .llm import APIGenerator
from .database import DatabaseService

main = Blueprint('main', __name__)

# Initialize components (lazy loading)
_retriever = None
_generator = None

UPLOAD_EXTENSIONS = {'.pdf', '.txt', '.md', '.doc', '.docx'}

def get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever(
            documents_dir=DOCUMENTS_DIR,
            vector_db_dir=VECTOR_DB_DIR,
            embedding_model_name=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            top_k=TOP_K
        )
        _retriever.initialize()
    return _retriever

def get_generator() -> APIGenerator:
    global _generator
    if _generator is None:
        _generator = APIGenerator()
    return _generator


# =========================
# Main Routes
# =========================

@main.route('/')
def index():
    """Render chat interface"""
    return render_template('index.html')

@main.route('/admin')
def admin():
    """Render admin dashboard"""
    return render_template('admin.html')

# =========================
# Chat API
# =========================

@main.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint with RAG, caching, and history"""
    from flask import current_app
    logger = current_app.logger
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    query = data['message'].strip()
    session_id = data.get('session_id', 'default')
    
    # Input validation
    if not query:
        return jsonify({'error': 'Empty message'}), 400
    
    if len(query) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters)'}), 400
    
    if len(session_id) > 50:
        return jsonify({'error': 'Invalid session ID'}), 400
    
    logger.info(f"Chat request: session={session_id[:8]}..., query_len={len(query)}")
    
    try:
        # Ensure session exists
        DatabaseService.create_session(session_id)
        
        # Save user message
        DatabaseService.add_message(session_id, "user", query)
        
        # Check cache first
        cached = DatabaseService.get_cached_response(query)
        if cached:
            response, sources, latency = cached
            DatabaseService.add_message(session_id, "assistant", response, sources, latency, cached=True)
            logger.info(f"Cache hit for query: {query[:50]}...")
            return jsonify({
                'response': response,
                'sources': sources,
                'latency': round(latency, 2),
                'cached': True,
                'session_id': session_id
            })
        
        # Get RAG context
        retriever = get_retriever()
        context = retriever.get_context(query)
        
        # Get conversation context for multi-turn
        conv_context = DatabaseService.get_recent_context(session_id, n_turns=2)
        
        # Enhance context with conversation history
        full_context = context
        if conv_context:
            full_context = f"Percakapan sebelumnya:\n{conv_context}\n\n---\n\n{context}"
        
        # Get sources
        results = retriever.retrieve(query)
        sources = [
            {'source': doc.metadata.get('source', 'unknown'), 'score': round(score, 3)}
            for doc, score in results
        ]
        
        # Generate response
        generator = get_generator()
        response, latency = generator.generate(
            query=query,
            context=full_context,
            system_prompt=SYSTEM_PROMPT
        )
        
        # Cache the response
        DatabaseService.cache_response(query, response, sources, latency)
        
        # Save assistant message
        DatabaseService.add_message(session_id, "assistant", response, sources, latency)
        
        logger.info(f"Generated response in {latency:.2f}s for session {session_id[:8]}...")
        
        return jsonify({
            'response': response,
            'sources': sources,
            'latency': round(latency, 2),
            'cached': False,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# =========================
# Session API
# =========================

@main.route('/api/session/new', methods=['POST'])
def new_session():
    """Create a new chat session"""
    session_id = DatabaseService.create_session()
    return jsonify({'session_id': session_id})

@main.route('/api/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """Get chat history for a session"""
    messages = DatabaseService.get_messages(session_id)
    return jsonify({'messages': messages})

# =========================
# Feedback API
# =========================

@main.route('/api/feedback', methods=['POST'])
def add_feedback():
    """Add feedback for a response"""
    data = request.get_json()
    
    session_id = data.get('session_id', 'default')
    message_id = data.get('message_index', 0)
    feedback = data.get('feedback')  # "positive" or "negative"
    query = data.get('query', '')
    response = data.get('response', '')
    
    if feedback not in ['positive', 'negative']:
        return jsonify({'error': 'Invalid feedback value'}), 400
    
    DatabaseService.add_feedback(session_id, message_id, feedback, query, response)
    
    return jsonify({'message': 'Feedback saved'})

# =========================
# Document Upload API
# =========================

@main.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process a document with full RAG indexing"""
    from flask import current_app
    from .rag import DocumentLoader
    
    logger = current_app.logger
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get category from form
    category = request.form.get('category', 'general')
    
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in UPLOAD_EXTENSIONS:
        return jsonify({'error': f'Invalid file type. Allowed: {list(UPLOAD_EXTENSIONS)}'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = DOCUMENTS_DIR / filename
        file.save(str(filepath))
        logger.info(f"File saved: {filepath}")
        
        # Create loader
        loader = DocumentLoader(
            documents_dir=DOCUMENTS_DIR,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # Convert if needed
        process_path = filepath
        converted = False
        if ext not in {'.md', '.markdown'}:
            try:
                md_path = loader.convert_to_markdown(filepath, DOCUMENTS_DIR)
                process_path = md_path
                converted = True
                logger.info(f"Converted to: {md_path}")
            except Exception as e:
                logger.warning(f"Conversion failed, using original: {e}")
        
        # Process and chunk document
        chunks = loader.load_document(process_path, category=category)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Add to vector store
        retriever = get_retriever()
        retriever.vector_store.add_documents(chunks)
        retriever.vector_store.save()
        logger.info("Added to vector store")
        
        # Save to database
        db_category = DatabaseService.get_category_by_name(category)
        DatabaseService.add_document(
            filename=process_path.name,
            category_id=db_category.id if db_category else None,
            file_size=process_path.stat().st_size,
            chunk_count=len(chunks),
            original_name=filename
        )
        
        return jsonify({
            'success': True,
            'message': f'Document processed successfully',
            'filename': process_path.name,
            'original_name': filename,
            'category': category,
            'chunks': len(chunks),
            'converted': converted
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main.route('/api/categories', methods=['GET'])
def list_categories():
    """List all document categories"""
    categories = DatabaseService.get_all_categories()
    return jsonify({'categories': categories})

@main.route('/api/documents', methods=['GET'])
def list_documents():
    """List all documents from database"""
    try:
        documents = DatabaseService.get_all_documents()
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/documents/<filename>', methods=['DELETE'])
def delete_document(filename):
    """Delete a document and remove from index"""
    try:
        # Delete from filesystem
        filepath = DOCUMENTS_DIR / secure_filename(filename)
        if filepath.exists():
            filepath.unlink()
        
        # Delete from database
        DatabaseService.delete_document(filename)
        
        return jsonify({'message': f'{filename} deleted', 'note': 'Run refresh to update index'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================
# Admin API
# =========================

@main.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Get admin statistics - all from database"""
    stats = DatabaseService.get_admin_stats()
    
    # Get document count and total chunks from database
    documents = DatabaseService.get_all_documents()
    stats['document_count'] = len(documents)
    stats['indexed_chunks'] = sum(d.get('chunk_count', 0) for d in documents)
    
    return jsonify(stats)

@main.route('/api/admin/feedback', methods=['GET'])
def admin_feedback():
    """Get all feedback"""
    feedback = DatabaseService.get_recent_feedback(limit=50)
    return jsonify({'feedback': feedback})

@main.route('/api/admin/sessions', methods=['GET'])
def admin_sessions():
    """Get all sessions"""
    sessions = DatabaseService.get_all_sessions()
    return jsonify({'sessions': sessions})

# =========================
# Utility API
# =========================

@main.route('/api/refresh', methods=['POST'])
def refresh_index():
    """Refresh the document index"""
    try:
        retriever = get_retriever()
        retriever.refresh_index()
        return jsonify({'message': 'Index refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'llm_ready': _generator is not None,
        'index_ready': _retriever is not None and _retriever._initialized
    })

@main.route('/api/sync', methods=['POST'])
def sync_documents():
    """Sync documents from filesystem to database"""
    from flask import current_app
    logger = current_app.logger
    
    try:
        synced = 0
        skipped = 0
        
        if not DOCUMENTS_DIR.exists():
            return jsonify({'error': 'Documents directory not found'}), 404
        
        # Get existing docs from DB
        existing = DatabaseService.get_all_documents()
        existing_names = {d['filename'] for d in existing}
        
        # Scan filesystem
        for filepath in DOCUMENTS_DIR.iterdir():
            if not filepath.is_file():
                continue
            
            # Skip if already in DB
            if filepath.name in existing_names:
                skipped += 1
                continue
            
            # Add to database
            try:
                DatabaseService.add_document(
                    filename=filepath.name,
                    category_id=None,  # Default category
                    file_size=filepath.stat().st_size,
                    chunk_count=0,  # Unknown
                    original_name=filepath.name
                )
                synced += 1
                logger.info(f"Synced: {filepath.name}")
            except Exception as e:
                logger.warning(f"Skip {filepath.name}: {e}")
        
        return jsonify({
            'message': f'Synced {synced} documents, skipped {skipped}',
            'synced': synced,
            'skipped': skipped
        })
        
    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
