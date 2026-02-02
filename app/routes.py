# -*- coding: utf-8 -*-
"""Flask routes for SINEMA Chatbot API - Database Version"""

import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

from .config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, MODEL_DIR, BASE_DIR,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_NEW_TOKENS, TEMPERATURE, TOP_P, DEVICE, SYSTEM_PROMPT,
    RELEVANCE_THRESHOLD
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
            top_k=TOP_K,
            use_reranker=False,  # Reranker dinonaktifkan
            relevance_threshold=RELEVANCE_THRESHOLD
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
        
        # # Check cache first (TEMPORARILY DISABLED)
        # cached = DatabaseService.get_cached_response(query)
        # if cached:
        #     cached_response, sources, original_latency = cached
        #     logger.info(f"Cache hit for query: {query[:50]}...")
        #     
        #     # Save to message log as cached
        #     DatabaseService.add_message(session_id, "assistant", cached_response, sources, original_latency, cached=True)
        #     
        #     return jsonify({
        #         'response': cached_response,
        #         'sources': sources,
        #         'latency': round(original_latency, 2),
        #         'cached': True,
        #         'session_id': session_id
        #     })
        # Fast pattern matching with text normalization
        import re
        
        # Normalize repeated letters (haiiii → hai, halooo → halo)
        def normalize_text(text):
            return re.sub(r'(.)\1{2,}', r'\1', text.lower().strip())
        
        query_normalized = normalize_text(query)
        
        # Greeting/simple message patterns (skip retrieval for these)
        greeting_patterns = ['halo', 'hai', 'hello', 'hi', 'hey', 'morning', 'selamat pagi', 'selamat siang', 
                           'selamat sore', 'selamat malam', 'terima kasih', 'thanks', 'makasih', 'thx',
                           'ok', 'oke', 'baik', 'siap', 'good morning', 'good afternoon']
        
        # Identity keywords - if query contains these combinations, skip retrieval
        identity_keywords = ['siapa kamu', 'kamu siapa', 'who are you', 'what can you do',
                             'kamu fungsinya', 'fungsi kamu', 'kamu bisa', 'bisa apa',
                             'tugas kamu', 'kamu itu', 'kamu untuk', 'kegunaan kamu']
        has_identity_keyword = ('kamu' in query_normalized and any(k in query_normalized for k in ['fungsi', 'bisa', 'tugas', 'apa', 'untuk', 'kegunaan'])) or \
                               any(k in query_normalized for k in identity_keywords)

        is_greeting = any(query_normalized == p or query_normalized.startswith(p + ' ') or
                          query_normalized.startswith(p + ',') or query_normalized.startswith(p + '?')
                          for p in greeting_patterns)

        # Simple queries: greetings OR identity questions (identity can be longer than 60 chars)
        is_simple_query = is_greeting or (has_identity_keyword and len(query_normalized) < 150)
        
        generator = get_generator()
        
        if is_simple_query:
            # Direct response without retrieval
            logger.info(f"Query classification: DIRECT for: {query[:50]}...")
            response, latency = generator.generate(
                query=query,
                context="",
                system_prompt=SYSTEM_PROMPT
            )
            logger.info(f"[DIRECT] Generated response in {latency:.2f}s for session {session_id[:8]}...")
            DatabaseService.add_message(session_id, "assistant", response, [], latency)
            return jsonify({
                'response': response,
                'sources': [],  # No sources for direct responses
                'latency': round(latency, 2),
                'session_id': session_id
            })
        
        # Get RAG context for actual questions
        retriever = get_retriever()
        context = retriever.get_context(query)

        # Early return if no relevant documents found (prevent hallucination)
        if not context or len(context.strip()) < 50:
            logger.warning(f"No relevant documents found for query: {query[:50]}...")
            return jsonify({
                'response': "Maaf, saya tidak menemukan informasi yang relevan tentang pertanyaan Anda dalam dokumen. Silakan coba pertanyaan lain atau hubungi admin FATEK untuk informasi lebih lanjut. 😊",
                'sources': [],
                'latency': 0.0,
                'session_id': session_id
            })
        
        # Get conversation context using sliding window + summary
        older_msgs, recent_msgs = DatabaseService.get_context_sliding_window(session_id, recent_turns=2)
        
        # Build conversation context
        conv_context_parts = []
        
        # Summarize older messages if any exist
        if older_msgs and len(older_msgs) >= 2:
            generator = get_generator()
            older_text = DatabaseService.format_messages_for_context(older_msgs, max_chars=200)
            
            # Generate summary of older conversation
            summary_prompt = f"""Ringkas percakapan berikut dalam 1-2 kalimat singkat. 
Fokus pada topik dan informasi penting yang dibahas. Gunakan bahasa Indonesia.

Percakapan:
{older_text}

Ringkasan singkat:"""
            
            summary, _ = generator.generate(
                query=summary_prompt,
                context="",
                system_prompt="Kamu adalah asisten yang bertugas meringkas percakapan secara singkat."
            )
            
            # Only add summary if it's not an error
            if summary and not any(err in summary.lower() for err in ['maaf,', 'error:', 'rate limit']):
                conv_context_parts.append(f"📝 Ringkasan percakapan sebelumnya:\n{summary.strip()}")
                logger.info(f"Generated conversation summary: {summary[:100]}...")
        
        # Add recent messages in full
        if recent_msgs:
            recent_text = DatabaseService.format_messages_for_context(recent_msgs, max_chars=500)
            conv_context_parts.append(f"💬 Percakapan terbaru:\n{recent_text}")
        
        # Combine everything
        full_context = context
        if conv_context_parts:
            conv_context = "\n\n---\n\n".join(conv_context_parts)
            full_context = f"{conv_context}\n\n---\n\n📚 Konteks dokumen:\n{context}"
        
        # Get sources with heading and snippet for source citation
        # Filter by relevance score and limit to top 5
        results = retriever.retrieve(query)
        sources = [
            {
                'source': doc.metadata.get('source', 'unknown'),
                'heading': doc.metadata.get('heading', ''),
                'snippet': doc.metadata.get('snippet', '')
            }
            for doc, score in results
            if score > 0.4  # Only include relevant sources
        ][:5]  # Limit to top 5
        
        # Generate response
        generator = get_generator()
        response, latency = generator.generate(
            query=query,
            context=full_context,
            system_prompt=SYSTEM_PROMPT
        )

        # Check if response is an error
        error_indicators = [
            'maaf,',
            'error:',
            'rate limit',
            'batas penggunaan',
            'server sedang tidak tersedia',
            'masalah autentikasi',
            'terjadi kesalahan'
        ]
        is_error_response = any(indicator in response.lower() for indicator in error_indicators)

        # For error responses, don't show sources
        if is_error_response:
            sources = []


        # Cache the response ONLY if it's a valid successful response
        # Skip caching error responses
        skip_query_patterns = [
            'ok', 'oke', 'baik', 'baiklah', 'hmm', 'oh', 'ya', 'yaa',
            'terima kasih', 'thanks', 'makasih', 'siap', 'mantap', 'lanjut',
            'halo', 'hai', 'hi', 'hello', 'hey'
        ]
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())  # Split into words
        is_short_query = len(query_lower) < 10  # Less than 10 chars
        # Only match if pattern is an EXACT WORD in query (not substring)
        is_generic_query = any(pattern in query_words or query_lower == pattern for pattern in skip_query_patterns)

        # # Cache the response if it's valid (TEMPORARILY DISABLED)
        # should_cache = not is_error_response and not is_short_query and not is_generic_query
        #
        # logger.info(f"[CACHE DEBUG] query='{query[:30]}...', is_error={is_error_response}, is_short={is_short_query}, is_generic={is_generic_query}, should_cache={should_cache}")
        #
        # if should_cache:
        #     DatabaseService.cache_response(query, response, sources, latency)
        # else:
        #     logger.info(f"[CACHE DEBUG] Skipped caching due to filters")
        
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

@main.route('/api/categories', methods=['GET', 'POST'])
def categories():
    """List all or create new document categories"""
    if request.method == 'GET':
        categories = DatabaseService.get_all_categories()
        return jsonify({'categories': categories})
    
    # POST - Create new category
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name', '').strip().lower().replace(' ', '_')
    display_name = data.get('display_name', '').strip()
    icon = data.get('icon', '📁')
    
    if not name or not display_name:
        return jsonify({'error': 'Name and display_name are required'}), 400
    
    # Check if exists
    existing = DatabaseService.get_category_by_name(name)
    if existing:
        return jsonify({'error': f'Category "{name}" already exists'}), 400
    
    # Create category
    category = DatabaseService.create_category(name, display_name, icon)
    if category:
        return jsonify({'success': True, 'category': category.to_dict()})
    else:
        return jsonify({'error': 'Failed to create category'}), 500

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
    """Delete a document, its original file, and refresh index to remove chunks"""
    from flask import current_app
    logger = current_app.logger
    
    try:
        safe_name = secure_filename(filename)
        base_name = Path(safe_name).stem
        deleted_files = []
        
        # Delete MD file
        md_path = DOCUMENTS_DIR / safe_name
        if md_path.exists():
            md_path.unlink()
            deleted_files.append(safe_name)
            logger.info(f"Deleted MD: {safe_name}")
        
        # Delete original files (PDF, DOC, DOCX)
        for ext in ['.pdf', '.doc', '.docx', '.txt']:
            orig_path = DOCUMENTS_DIR / f"{base_name}{ext}"
            if orig_path.exists():
                orig_path.unlink()
                deleted_files.append(f"{base_name}{ext}")
                logger.info(f"Deleted original: {base_name}{ext}")
        
        # Delete from database
        deleted = DatabaseService.delete_document_by_filename(filename)
        logger.info(f"Deleted from database: {filename} (success: {deleted})")
        
        # Clear all cache since document content changed
        cache_cleared = DatabaseService.clear_all_cache()
        logger.info(f"Cleared {cache_cleared} cache entries due to document deletion")
        
        # Schedule background reindex (debounced - waits 5s after last delete)
        try:
            from .background_reindex import get_background_reindex_service
            bg_service = get_background_reindex_service()
            bg_service.schedule_reindex()
            logger.info("Background reindex scheduled (5s debounce)")
        except Exception as e:
            logger.warning(f"Failed to schedule background reindex: {e}")
        
        return jsonify({
            'message': 'Document deleted successfully',
            'deleted_files': deleted_files,
            'reindex_scheduled': True,
            'note': 'Index will refresh automatically in 5 seconds'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/documents/<filename>/download', methods=['GET'])
def download_document(filename):
    """Download a document"""
    from flask import send_from_directory
    try:
        safe_filename = secure_filename(filename)
        filepath = DOCUMENTS_DIR / safe_filename
        
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(
            DOCUMENTS_DIR,
            safe_filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/documents/<filename>/preview', methods=['GET'])
def preview_document(filename):
    """Preview a document (inline display)"""
    from flask import send_from_directory
    try:
        safe_filename = secure_filename(filename)
        filepath = DOCUMENTS_DIR / safe_filename
        
        if not filepath.exists():
            return jsonify({'error': 'Resource not found'}), 404
        
        # Get mimetype
        ext = filepath.suffix.lower()
        mimetypes = {
            '.pdf': 'application/pdf',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        mimetype = mimetypes.get(ext, 'application/octet-stream')
        
        return send_from_directory(
            DOCUMENTS_DIR,
            safe_filename,
            as_attachment=False,
            mimetype=mimetype
        )
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

@main.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache entries"""
    from flask import current_app
    try:
        deleted = DatabaseService.clear_all_cache()
        current_app.logger.info(f"Manually cleared {deleted} cache entries")
        return jsonify({
            'message': 'Cache cleared successfully',
            'deleted_count': deleted
        })
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
