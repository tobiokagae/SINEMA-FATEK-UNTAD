# -*- coding: utf-8 -*-
"""
SINEMA RAG Chatbot - Streamlit UI
Universitas Tadulako
"""
import streamlit as st
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, MODEL_DIR,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_NEW_TOKENS, TEMPERATURE, TOP_P, DEVICE, SYSTEM_PROMPT
)
from app.rag import RAGRetriever
from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import EmbeddingModel
import os
from dotenv import load_dotenv
load_dotenv()

# Choose generator based on USE_API setting
USE_API = os.getenv('USE_API', 'false').lower() == 'true'

if USE_API:
    from app.llm.api_generator import APIGenerator as LLMGenerator
    print("🌐 Using OpenRouter API Generator")
else:
    from app.llm import LLMGenerator
    print("💻 Using Local LLM Generator")

# =========================
# Database Setup for Streamlit
# =========================
from flask import Flask
from app.config import DATABASE_URL
from app.models import db, Category, Document
from app.database import DatabaseService

@st.cache_resource
def get_flask_app():
    """Create minimal Flask app for database operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    db.init_app(app)
    with app.app_context():
        db.create_all()
        DatabaseService.seed_default_categories()
    return app

# Initialize Flask app for database
_flask_app = get_flask_app()


# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="SINEMA Chatbot - Universitas Tadulako",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS
# =========================
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-align: center;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.8);
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        color: #e2e8f0;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        max-width: 80%;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Source box */
    .source-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 3px solid #667eea;
        padding: 0.5rem 1rem;
        margin-top: 0.5rem;
        border-radius: 0 10px 10px 0;
        font-size: 0.85rem;
    }
    
    /* Stats card */
    .stat-card {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stat-label {
        color: #a0aec0;
        font-size: 0.9rem;
    }
    
    /* Document card */
    .doc-card {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* Success/info boxes */
    .success-box {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# =========================
# Session State Initialization
# =========================
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'retriever' not in st.session_state:
    st.session_state.retriever = None

if 'generator' not in st.session_state:
    st.session_state.generator = None

if 'documents_processed' not in st.session_state:
    st.session_state.documents_processed = {}

# =========================
# Helper Functions
# =========================
def get_index_timestamp():
    """Get modification time of index file for cache invalidation"""
    index_path = VECTOR_DB_DIR / "index.faiss"
    if index_path.exists():
        return int(index_path.stat().st_mtime)
    return 0

@st.cache_resource(show_spinner=False)
def load_retriever(_index_timestamp: int):
    """Load RAG retriever (cached, invalidates when index changes)"""
    print("🔄 Loading RAG Retriever...")
    retriever = RAGRetriever(
        documents_dir=DOCUMENTS_DIR,
        vector_db_dir=VECTOR_DB_DIR,
        embedding_model_name=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        top_k=TOP_K
    )
    retriever.initialize()
    print("✅ RAG Retriever loaded!")
    return retriever

@st.cache_resource(show_spinner=False)
def load_generator():
    """Load LLM generator (cached) - API or Local based on USE_API setting"""
    print("🔄 Loading LLM Generator...")
    
    if USE_API:
        # API Generator - no arguments needed
        generator = LLMGenerator()
    else:
        # Local Generator - needs model path and settings
        generator = LLMGenerator(
            model_path=MODEL_DIR,
            device=DEVICE,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P
        )
        # PRELOAD THE MODEL AT STARTUP
        _ = generator.model  # This triggers lazy loading
    
    print("✅ LLM Generator loaded!")
    return generator

# =========================
# PRELOAD MODELS AT STARTUP
# =========================
# This runs once when the server starts, not on every request
with st.spinner("🚀 Memuat model AI (hanya sekali saat startup)..."):
    _cached_retriever = load_retriever(get_index_timestamp())
    _cached_generator = load_generator()

def get_document_list():
    """Get list of documents in the documents directory"""
    if not DOCUMENTS_DIR.exists():
        return []
    
    docs = []
    for f in DOCUMENTS_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in {'.pdf', '.txt', '.md'}:
            docs.append({
                'name': f.name,
                'size': f.stat().st_size,
                'type': f.suffix[1:].upper(),
                'modified': datetime.fromtimestamp(f.stat().st_mtime)
            })
    return docs

def rewrite_query(user_query: str, generator) -> str:
    """
    Use LLM to understand and rewrite user query into search-friendly keywords.
    This improves retrieval by converting conversational questions to keyword-based search.
    """
    rewrite_prompt = f"""Tugas: Ubah pertanyaan user berikut menjadi kata kunci pencarian yang efektif untuk mencari di dokumen akademik.

Pertanyaan user: "{user_query}"

Instruksi:
1. Pahami maksud sebenarnya dari pertanyaan user
2. Ekstrak konsep-konsep kunci yang perlu dicari
3. Tulis ulang sebagai kata kunci pencarian (bukan kalimat lengkap)
4. Gunakan istilah akademik formal yang mungkin ada di dokumen

Contoh:
- "kalau dapat B bisa mengulang untuk dapat A tidak?" → "pengulangan mata kuliah perbaikan nilai syarat"
- "berapa lama waktu kuliah sampai lulus?" → "masa studi maksimal semester program sarjana"
- "gimana cara ngurus skripsi?" → "prosedur tugas akhir skripsi persyaratan pendaftaran"

Kata kunci pencarian:"""

    try:
        # Generate rewritten query using LLM
        result = generator.generate(
            query=rewrite_prompt,
            context="",  # No context needed for query rewriting
            conversation_history=[]
        )
        # Result is (response, latency) tuple - extract response
        rewritten = result[0] if isinstance(result, tuple) else result
        # Clean up the response - take first line, remove quotes and extra spaces
        rewritten = rewritten.strip().split('\n')[0].strip('"\'').strip()
        # If response is too long or empty, use original query
        if len(rewritten) < 5 or len(rewritten) > 200:
            return user_query
        return rewritten
    except Exception as e:
        print(f"Query rewriting failed: {e}")
        return user_query  # Fallback to original query

def process_uploaded_file(uploaded_file):
    """Process and save uploaded file"""
    # Save file
    save_path = DOCUMENTS_DIR / uploaded_file.name
    with open(save_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    return save_path

def format_file_size(size_bytes):
    """Format file size to human readable"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024*1024):.1f} MB"

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("### 🎓 SINEMA Chatbot")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📍 Navigasi",
        ["💬 Chat", "📁 Dokumen", "⚙️ Pengaturan"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    docs = get_document_list()
    st.markdown("### 📊 Statistik")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Dokumen", len(docs))
    with col2:
        st.metric("Pesan", len(st.session_state.messages))
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =========================
# Main Content
# =========================

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🎓 SINEMA Chatbot</h1>
    <p class="header-subtitle">Asisten Akademik Fakultas Teknik - Universitas Tadulako</p>
</div>
""", unsafe_allow_html=True)

# =========================
# Chat Page
# =========================
if page == "💬 Chat":
    
    # Load models
    with st.spinner("🔄 Memuat model AI..."):
        retriever = load_retriever(get_index_timestamp())
        generator = load_generator()
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Display assistant message with proper markdown rendering
                content = str(message["content"]).strip()
                
                # Use container with custom styling
                with st.container():
                    st.markdown(f"""
                    <div class="assistant-message">
                    """, unsafe_allow_html=True)
                    
                    # Render markdown content natively
                    st.markdown(content)
                    
                    # Display sources if any (but not for error messages)
                    is_error_response = any(err in content for err in ['⚠️', '🔐', '⏱️', '🔧', '❌ **'])
                    if message.get("sources") and not is_error_response:
                        sources_list = ", ".join([s['source'] for s in message['sources'][:3]])
                        st.caption(f"📚 Sumber: {sources_list}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Display response time
                if message.get("latency") and message["latency"] > 0:
                    st.caption(f"⚡ Response time: {message['latency']:.2f}s")
    
    # Chat input
    st.markdown("---")
    
    # Suggested questions (only show if no messages yet)
    if len(st.session_state.messages) == 0:
        st.markdown("**💡 Pertanyaan yang sering ditanyakan:**")
        suggested_questions = [
            "📚 Apa syarat untuk mengambil Tugas Akhir?",
            "⚖️ Apa sanksi plagiarisme?",
            "🎓 Berapa beban SKS maksimal per semester?",
            "🌐 Bagaimana cara mendapatkan poin SINEMA?",
            "📋 Bagaimana cara mengunduh TEM?"
        ]
        cols = st.columns(3)
        for i, q in enumerate(suggested_questions[:3]):
            with cols[i]:
                if st.button(q, key=f"suggest_{i}", use_container_width=True):
                    st.session_state.pending_question = q.split(" ", 1)[1]  # Remove emoji
                    st.rerun()
    
    # Check for pending question from suggested buttons
    if 'pending_question' in st.session_state and st.session_state.pending_question:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None
        send_button = True
    else:
        col1, col2 = st.columns([6, 1])
        
        with col1:
            # Use unique key based on message count to clear input
            user_input = st.text_input(
                "Ketik pertanyaan...",
                placeholder="Contoh: Apa syarat mengambil TA?",
                label_visibility="collapsed",
                key=f"chat_input_{len(st.session_state.messages)}"
            )
        
        with col2:
            send_button = st.button("Kirim 📤", use_container_width=True)
    
    # Process input
    if send_button and user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Generate response
        with st.spinner("🤔 Sedang berpikir..."):
            try:
                query_lower = user_input.lower().strip()
                
                # Detect greeting/about-bot questions - these don't need RAG
                # These patterns must be at START of query or be the ENTIRE query
                greeting_exact = ['hai', 'halo', 'hello', 'hi', 'hey', 'hei', 'haloo', 'halloo']
                greeting_patterns = [
                    'siapa kamu', 'kamu siapa', 'siapa km', 'km siapa',
                    'kamu itu apa', 'apa itu kamu', 'kamu apa sih', 'apa kamu ini',
                    'kalo kamu siapa', 'kalau kamu siapa', 'kamu ini apa', 'kamu ini siapa',
                    'bisa apa kamu', 'kamu bisa apa', 'apa yang bisa kamu', 'fungsimu apa',
                    'perkenalkan dirimu', 'perkenalkan diri'
                ]
                
                # Separate thank you patterns
                thankyou_patterns = ['thanks', 'terima kasih', 'makasih', 'thx', 'tq', 'thank you']
                
                # Casual closing responses - short phrases that end conversation
                casual_closing = ['tidak ada', 'nda ada', 'ga ada', 'gak ada', 'ngga ada',
                                  'oke', 'ok', 'baik', 'sip', 'siap', 'sudah', 'cukup',
                                  'iya', 'ya', 'yap', 'yup', 'nope', 'tidak', 'nggak', 'enggak']
                
                # Check greeting: exact match for short greetings, or pattern at START of query
                is_greeting = (
                    query_lower in greeting_exact or 
                    any(query_lower.startswith(p) for p in greeting_patterns) or
                    any(query_lower == p for p in greeting_patterns)
                ) and len(query_lower) < 50
                is_thankyou = any(p in query_lower for p in thankyou_patterns) and len(query_lower) < 30
                is_casual_closing = query_lower in casual_closing or (len(query_lower) < 15 and any(p == query_lower for p in casual_closing))
                
                if is_thankyou:
                    # Simple thank you response - no LLM needed
                    response = "Sama-sama! 😊 Senang bisa membantu. Ada lagi yang ingin ditanyakan?"
                    latency = 0.0
                    context = ""
                    sources = []
                elif is_casual_closing:
                    # Casual closing response - no LLM needed
                    response = "Baik! 👍 Jika ada pertanyaan lain seputar akademik, silakan tanyakan ya!"
                    latency = 0.0
                    context = ""
                    sources = []
                elif is_greeting:
                    # Direct response for greetings - no RAG needed
                    context = ""
                    sources = []
                    # Use special greeting prompt
                    greeting_prompt = """Kamu adalah SINEMA Bot, asisten akademik Fakultas Teknik Universitas Tadulako.
Jawab dengan ramah dan perkenalkan dirimu secara SINGKAT. JANGAN tampilkan disclaimer apapun.
Jelaskan bahwa kamu bisa membantu tentang: KRS, UKT, skripsi, beasiswa, dan layanan akademik lainnya."""
                    response, latency = generator.generate(
                        query=user_input,
                        context="",
                        system_prompt=greeting_prompt,
                        conversation_history=st.session_state.messages
                    )
                else:
                    # Check cache first for similar questions
                    cached_info = None
                    with _flask_app.app_context():
                        cached = DatabaseService.get_cached_response(user_input)
                        if cached:
                            cached_response, sources, cached_latency = cached
                            cached_info = cached_response
                    
                    if cached_info:
                        # SMART CACHE: Use cached response as context, but let LLM adapt to current question
                        st.caption("⚡ Smart cache - menyesuaikan jawaban...")
                        adapt_prompt = f"""Kamu adalah asisten akademik. Berikut adalah informasi yang sudah diketahui tentang topik ini:

INFORMASI TERSIMPAN:
{cached_info}

PERTANYAAN USER SAAT INI:
{user_input}

Tugas: Jawab pertanyaan user berdasarkan informasi di atas. Sesuaikan jawaban agar relevan dengan cara user bertanya, tapi jangan ubah fakta yang ada. Gunakan bahasa yang ramah dan emoji 😊"""
                        
                        response, latency = generator.generate(
                            query=adapt_prompt,
                            context="",
                            system_prompt="Kamu adalah SINEMA Bot, asisten akademik yang membantu mahasiswa.",
                            conversation_history=[]
                        )
                    else:
                        # Step 1: Rewrite query for better retrieval
                        search_query = rewrite_query(user_input, generator)
                        if search_query != user_input:
                            st.caption(f"🔍 Mencari: {search_query}")
                        
                        # Step 2: Get RAG context using rewritten query
                        results = retriever.retrieve(search_query)
                        
                        # Use documents with relevance score > 0.01 (low threshold for better recall)
                        RELEVANCE_THRESHOLD = 0.01
                        relevant_results = [(doc, score) for doc, score in results if score > RELEVANCE_THRESHOLD]
                        
                        if relevant_results:
                            # Build context from relevant documents with safe access
                            context_parts = []
                            sources = []
                            for doc, score in relevant_results:
                                try:
                                    content = getattr(doc, 'page_content', str(doc))
                                    context_parts.append(content)
                                    source = doc.metadata.get('source', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
                                    sources.append({'source': source, 'score': round(score, 3)})
                                except Exception as e:
                                    print(f"Error accessing document: {e}")
                                    continue
                            context = "\n\n".join(context_parts)
                        else:
                            # No relevant documents
                            context = ""
                            sources = []
                        
                        # Use LLM with RAG context and conversation history
                        response, latency = generator.generate(
                            query=user_input,
                            context=context,
                            system_prompt=SYSTEM_PROMPT,
                            conversation_history=st.session_state.messages
                        )
                        
                        # Cache the response
                        with _flask_app.app_context():
                            DatabaseService.cache_response(user_input, response, sources, latency)
                
                # Clean response from any HTML tags that might leak
                import re
                response = re.sub(r'<[^>]+>', '', response)
                
                # Clear sources if response is an error message
                error_indicators = ['⚠️', '🔐', '⏱️', '🔧', '❌ **']
                if any(err in response for err in error_indicators):
                    sources = []
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources,
                    "latency": latency
                })
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.rerun()

# =========================
# Documents Page
# =========================
elif page == "📁 Dokumen":
    
    st.markdown("### 📁 Manajemen Dokumen")
    st.markdown("Upload dan kelola dokumen untuk knowledge base chatbot.")
    
    # Upload section
    st.markdown("---")
    st.markdown("#### 📤 Upload Dokumen Baru")
    
    # Get categories from database
    with _flask_app.app_context():
        db_categories = DatabaseService.get_all_categories()
    
    # Build category options from database
    DOCUMENT_CATEGORIES = {cat['name']: f"{cat['icon']} {cat['display_name']}" for cat in db_categories}
    
    uploaded_file = st.file_uploader(
        "Pilih file (PDF, Word, Markdown, atau Text)",
        type=['pdf', 'md', 'txt', 'doc', 'docx'],
        help="Semua file akan dikonversi ke Markdown untuk pemrosesan yang lebih baik"
    )
    
    if uploaded_file:
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.info(f"📄 **{uploaded_file.name}** ({format_file_size(uploaded_file.size)})")
        
        with col2:
            # Category dropdown from database
            selected_category = st.selectbox(
                "Kategori",
                options=list(DOCUMENT_CATEGORIES.keys()),
                format_func=lambda x: DOCUMENT_CATEGORIES[x],
                label_visibility="collapsed"
            )
        
        with col3:
            if st.button("⬆️ Upload & Proses", use_container_width=True):
                with st.spinner("🔄 Memproses dokumen..."):
                    try:
                        # Save file
                        save_path = process_uploaded_file(uploaded_file)
                        
                        # Create loader
                        loader = DocumentLoader(
                            documents_dir=DOCUMENTS_DIR,
                            chunk_size=CHUNK_SIZE,
                            chunk_overlap=CHUNK_OVERLAP
                        )
                        
                        # Check if non-markdown file - convert to Markdown first
                        converted_md_path = None
                        if save_path.suffix.lower() not in {'.md', '.markdown'}:
                            file_type = save_path.suffix.upper().replace('.', '')
                            with st.spinner(f"📄 Mengkonversi {file_type} ke Markdown..."):
                                try:
                                    converted_md_path = loader.convert_to_markdown(save_path, DOCUMENTS_DIR)
                                    st.info(f"📄 {file_type} dikonversi ke: {converted_md_path.name}")
                                    # Process the markdown file instead
                                    process_path = converted_md_path
                                except Exception as e:
                                    st.warning(f"⚠️ Konversi gagal, memproses file langsung: {e}")
                                    process_path = save_path
                        else:
                            process_path = save_path
                        
                        # Process document with category
                        chunks = loader.load_document(process_path, category=selected_category)
                        
                        # Add to vector store
                        retriever = load_retriever(get_index_timestamp())
                        retriever.vector_store.add_documents(chunks)
                        retriever.vector_store.save()
                        
                        # Save to database (use original filename for reference)
                        with _flask_app.app_context():
                            category = DatabaseService.get_category_by_name(selected_category)
                            # Save both original and converted file info
                            DatabaseService.add_document(
                                filename=process_path.name,  # Use processed file name
                                category_id=category.id if category else None,
                                file_size=process_path.stat().st_size,
                                chunk_count=len(chunks),
                                original_name=uploaded_file.name  # Keep original name
                            )
                        
                        # Build success message
                        msg = f"""
                        ✅ **Dokumen berhasil diproses!**
                        - File asli: {uploaded_file.name}"""
                        
                        if converted_md_path:
                            msg += f"""
                        - Dikonversi ke: {converted_md_path.name}"""
                        
                        msg += f"""
                        - Kategori: {DOCUMENT_CATEGORIES[selected_category]}
                        - Chunks: {len(chunks)}
                        - Status: Indexed & Saved to DB
                        """
                        
                        st.success(msg)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # Document list from database
    st.markdown("---")
    st.markdown("#### 📚 Daftar Dokumen")
    
    # Get documents from database
    with _flask_app.app_context():
        db_docs = DatabaseService.get_all_documents()
    
    if not db_docs:
        st.info("📭 Belum ada dokumen di database. Upload dokumen pertama Anda!")
    else:
        # Header
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        with col1:
            st.markdown("**Nama File**")
        with col2:
            st.markdown("**Kategori**")
        with col3:
            st.markdown("**Ukuran**")
        with col4:
            st.markdown("**Chunks**")
        with col5:
            st.markdown("**Aksi**")
        
        st.markdown("---")
        
        for doc in db_docs:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            
            with col1:
                st.markdown(f"📄 **{doc['filename']}**")
            
            with col2:
                if doc['category']:
                    cat = doc['category']
                    st.markdown(f"{cat['icon']} {cat['display_name']}")
                else:
                    st.markdown("❓ Uncategorized")
            
            with col3:
                st.markdown(f"{format_file_size(doc['file_size'])}")
            
            with col4:
                st.markdown(f"{doc['chunk_count']} chunks")
            
            with col5:
                if st.button("🗑️", key=f"del_{doc['id']}", help="Hapus dokumen"):
                    try:
                        # Delete from filesystem
                        file_path = DOCUMENTS_DIR / doc['filename']
                        if file_path.exists():
                            file_path.unlink()
                        
                        # Delete from database
                        with _flask_app.app_context():
                            DatabaseService.delete_document(doc['id'])
                        
                        st.success(f"Dokumen {doc['filename']} dihapus!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            st.markdown("---")
    
    # Add new category section
    st.markdown("#### ➕ Tambah Kategori Baru")
    
    with st.expander("Klik untuk menambah kategori", expanded=False):
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_cat_name = st.text_input(
                "Nama (tanpa spasi)", 
                placeholder="contoh: panduan_krs",
                help="Gunakan huruf kecil dan underscore"
            )
        
        with col2:
            new_cat_display = st.text_input(
                "Nama Tampilan",
                placeholder="contoh: Panduan KRS"
            )
        
        with col3:
            new_cat_icon = st.text_input(
                "Icon",
                placeholder="📝",
                max_chars=2
            )
        
        if st.button("➕ Tambah Kategori", use_container_width=True):
            if new_cat_name and new_cat_display:
                try:
                    with _flask_app.app_context():
                        from app.models import Category
                        # Check if exists
                        existing = db.session.query(Category).filter_by(name=new_cat_name).first()
                        if existing:
                            st.error(f"Kategori '{new_cat_name}' sudah ada!")
                        else:
                            new_cat = Category(
                                name=new_cat_name.lower().replace(' ', '_'),
                                display_name=new_cat_display,
                                icon=new_cat_icon or '📄'
                            )
                            db.session.add(new_cat)
                            db.session.commit()
                            st.success(f"✅ Kategori '{new_cat_display}' berhasil ditambahkan!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Nama dan Nama Tampilan harus diisi!")
    
    # Rebuild index button
    st.markdown("#### 🔄 Rebuild Index")
    st.warning("⚠️ Gunakan ini jika ada perubahan dokumen yang tidak terdeteksi.")
    
    if st.button("🔄 Rebuild Seluruh Index", use_container_width=True):
        with st.spinner("🔄 Rebuilding index..."):
            try:
                # Clear cache and reload
                load_retriever.clear()
                retriever = load_retriever(get_index_timestamp())
                retriever.refresh_index()
                st.success("✅ Index berhasil di-rebuild!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# =========================
# Settings Page
# =========================
elif page == "⚙️ Pengaturan":
    
    st.markdown("### ⚙️ Pengaturan Sistem")
    
    # Model info
    st.markdown("#### 🤖 Model Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">LLM Model</div>
            <div class="stat-value" style="font-size: 1rem;">GPT-4o-mini (OpenRouter)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">Mode</div>
            <div class="stat-value" style="font-size: 1.5rem;">☁️ API Cloud</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # RAG Configuration
    st.markdown("#### 📊 RAG Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Chunk Size", CHUNK_SIZE)
    with col2:
        st.metric("Chunk Overlap", CHUNK_OVERLAP)
    with col3:
        st.metric("Top K", TOP_K)
    
    st.markdown("---")
    
    # LLM Configuration
    st.markdown("#### 🧠 LLM Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Max Tokens", MAX_NEW_TOKENS)
    with col2:
        st.metric("Temperature", TEMPERATURE)
    with col3:
        st.metric("Top P", TOP_P)
    
    st.markdown("---")
    
    # Paths
    st.markdown("#### 📂 Paths")
    st.code(f"""
Documents: {DOCUMENTS_DIR}
Vector DB: {VECTOR_DB_DIR}
LLM API: OpenRouter (GPT-4o-mini)
    """)
    
    st.markdown("---")
    
    # System prompt
    st.markdown("#### 📝 System Prompt")
    st.text_area("System Prompt", SYSTEM_PROMPT, height=200, disabled=True)

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 1rem;">
    🎓 SINEMA Chatbot - Universitas Tadulako © 2025<br>
    <small>Powered by GPT-4o-mini + RAG</small>
</div>
""", unsafe_allow_html=True)
