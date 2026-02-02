# 🤖 SINEMA RAG Chatbot

> **Retrieval-Augmented Generation Chatbot untuk Sistem Informasi Akademik**
> Fakultas Teknik - Universitas Tadulako

## 📋 Deskripsi

Sistem chatbot berbasis RAG (Retrieval-Augmented Generation) yang terintegrasi dengan SINEMA untuk menjawab pertanyaan seputar akademik mahasiswa Fakultas Teknik UNTAD.

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **RAG Pipeline** | Dokumen di-chunk dan di-embed untuk retrieval semantik |
| **Query Rewriting** | LLM memahami konteks pertanyaan sebelum search |
| **Semantic Cache** | Cache respons untuk query serupa |
| **Background Reindex** | Debounced reindexing (5s delay) saat dokumen diubah |
| **Multi-format Support** | PDF, DOCX, DOC, TXT, MD dengan konversi otomatis |
| **Table Extraction** | Ekstraksi tabel dari PDF ke format markdown |
| **FAISS Vector Store** | Penyimpanan embedding yang efisien |
| **REST API** | Flask API untuk integrasi dengan Laravel SINEMA |

## 🏗️ Arsitektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Laravel/SINEMA │────▶│  Flask REST API  │────▶│   RAG Pipeline  │
│  (Frontend)     │     │  (Backend)       │     │   + LLM         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌──────────────┐         ┌──────────────┐
                        │    MySQL     │         │ FAISS Index  │
                        │  (Sessions)  │         │  (Vectors)   │
                        └──────────────┘         └──────────────┘
```

## 🔧 Konfigurasi

| Parameter | Nilai | Deskripsi |
|-----------|-------|-----------|
| Chunk Size | 800 chars | Ukuran potongan dokumen (untuk konteks lengkap) |
| Chunk Overlap | 200 chars | Overlap antar chunk (25% untuk menjaga kontinuitas) |
| Top-K | 20 | Jumlah chunk diambil per query (meningkatkan akurasi) |
| Relevance Threshold | 0.2 | Batas minimum relevansi |
| Embedding Model | `paraphrase-multilingual-MiniLM-L12-v2` | Model multilingual untuk Bahasa Indonesia |
| LLM | `openai/gpt-oss-20b:free` via OpenRouter | Model untuk generate jawaban |
| Temperature | 0.2 | Kreativitas jawaban (rendah untuk mengurangi halusinasi) |
| Max Tokens | 2048 | Panjang maksimal respons |

## ⚙️ Instalasi

### 1. Clone & Setup Virtual Environment
```bash
cd sinema-chatbot
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment
Salin `.env.example` ke `.env` dan isi:
```env
# Flask
SECRET_KEY=your-secret-key
DEBUG=true
FLASK_ENV=development

# OpenRouter API
USE_API=true
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=openai/gpt-oss-20b:free
DEVICE=cuda

# LLM Generation
MAX_NEW_TOKENS=2048
TEMPERATURE=0.2
TOP_P=0.9

# RAG Configuration
TOP_K=20
CHUNK_SIZE=800
CHUNK_OVERLAP=200
RELEVANCE_THRESHOLD=0.2

# Rate Limiting
RATE_LIMIT=20 per minute

# Database (MySQL)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=siny1585_sinemadb
DB_USERNAME=root
DB_PASSWORD=
```

## ▶️ Menjalankan

### Flask API (Untuk integrasi SINEMA)
```bash
flask run
# atau
python run.py
```
API tersedia di: `http://127.0.0.1:5000`

### Streamlit UI (Standalone)
```bash
streamlit run streamlit_app.py
```
UI tersedia di: `http://localhost:8501`

## 📡 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/chat` | Kirim pesan chat |
| `POST` | `/api/session/new` | Buat session baru |
| `GET` | `/api/session/<id>/history` | Riwayat chat session |
| `POST` | `/api/feedback` | Kirim feedback |
| `GET` | `/api/documents` | Daftar dokumen |
| `POST` | `/api/upload` | Upload dokumen baru |
| `DELETE` | `/api/documents/<filename>` | Hapus dokumen |
| `GET` | `/api/documents/<filename>/download` | Download dokumen |
| `GET` | `/api/documents/<filename>/preview` | Preview dokumen |
| `GET` | `/api/categories` | Daftar kategori |
| `POST` | `/api/categories` | Buat kategori baru |
| `POST` | `/api/refresh` | Refresh index manual |
| `POST` | `/api/cache/clear` | Hapus semua cache |
| `POST` | `/api/sync` | Sync dokumen filesystem ke database |
| `GET` | `/api/admin/stats` | Statistik sistem |
| `GET` | `/api/admin/feedback` | Daftar feedback |
| `GET` | `/api/admin/sessions` | Daftar sessions |
| `GET` | `/api/health` | Health check |

## 📁 Struktur Project

```
sinema-chatbot/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes.py             # API endpoints
│   ├── database.py           # Database service (MySQL)
│   ├── models.py             # SQLAlchemy models
│   ├── config.py             # Konfigurasi
│   ├── background_reindex.py # Background reindex service
│   ├── logging_config.py     # Logging configuration
│   ├── llm/                  # LLM integration
│   │   └── api_generator.py  # OpenRouter API generator
│   ├── rag/                  # RAG components
│   │   ├── __init__.py       # Module exports
│   │   ├── retriever.py      # RAG retriever
│   │   ├── vector_store.py   # FAISS vector store
│   │   ├── document_loader.py # Document loading & chunking
│   │   └── ...
│   └── templates/            # HTML templates
├── documents/                # Folder dokumen (MD + original)
├── vector_db/                # FAISS index storage
├── logs/                     # Log files
├── evaluation/               # Evaluasi RAG
├── static/                   # Static assets
├── .env                      # Environment config
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── run.py                    # Flask entry point
├── streamlit_app.py          # Streamlit UI
├── rebuild_index.py          # Manual index rebuild
├── evaluate_rag.py           # RAG evaluation script
└── verify_rag_system.py      # RAG verification
```

## 📝 Menambah Dokumen

### Via Laravel Admin (Recommended)
1. Login ke SINEMA sebagai admin
2. Buka menu **Chatbot > Dokumen Chatbot**
3. Upload file (PDF/DOCX/TXT/MD)
4. Pilih kategori
5. Klik **Upload & Proses**

### Via API
```bash
curl -X POST http://127.0.0.1:5000/api/upload \
  -F "file=@dokumen.pdf" \
  -F "category=akademik"
```

## 🔄 Background Reindex

Saat dokumen dihapus/ditambah, sistem secara otomatis:
1. Menjadwalkan reindex dengan delay 5 detik
2. Jika ada operasi lain dalam 5 detik, timer reset
3. Reindex hanya dijalankan sekali setelah semua operasi selesai

## 📊 Monitoring

Cek status sistem:
```bash
curl http://127.0.0.1:5000/api/admin/stats
```

Cek health:
```bash
curl http://127.0.0.1:5000/api/health
```

## 🛠️ Development

### Rebuild Index Manual
```bash
python rebuild_index.py
```

### Evaluate RAG Performance
```bash
python evaluate_rag.py
```

### Verify RAG System
```bash
python verify_rag_system.py
```

### Clear Cache
```bash
python clear_tem_cache.py
```

## 📝 License

Proyek skripsi - Fakultas Teknik Universitas Tadulako
