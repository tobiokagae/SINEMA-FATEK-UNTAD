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
| Chunk Size | 400 chars | Ukuran potongan dokumen |
| Chunk Overlap | 100 chars | Overlap antar chunk |
| Top-K | 25 | Jumlah chunk diambil per query |
| Embedding Model | `paraphrase-multilingual-MiniLM-L12-v2` | Model multilingual |
| LLM | GPT-4o-mini via OpenRouter | Model untuk generate jawaban |

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
# API Keys
OPENROUTER_API_KEY=your-openrouter-api-key

# Database (MySQL)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=siny1585_sinemadb
DB_USERNAME=root
DB_PASSWORD=

# Settings
USE_API=true
```

## ▶️ Menjalankan

### Flask API (Untuk integrasi SINEMA)
```bash
flask run
```
API tersedia di: `http://127.0.0.1:5000`

### Streamlit UI (Standalone)
```bash
streamlit run streamlit_app.py
```
UI tersedia di: `http://localhost:8501`

## � API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/chat` | Kirim pesan chat |
| `GET` | `/api/documents` | Daftar dokumen |
| `POST` | `/api/documents` | Upload dokumen baru |
| `DELETE` | `/api/documents/<filename>` | Hapus dokumen |
| `POST` | `/api/refresh` | Refresh index manual |
| `GET` | `/api/stats` | Statistik sistem |
| `GET` | `/api/categories` | Daftar kategori |

## 📁 Struktur Project

```
sinema-chatbot/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py             # API endpoints
│   ├── database.py           # Database service
│   ├── models.py             # SQLAlchemy models
│   ├── config.py             # Konfigurasi
│   ├── background_reindex.py # Background reindex service
│   └── rag/
│       ├── retriever.py      # RAG retriever
│       ├── vector_store.py   # FAISS vector store
│       ├── chunking.py       # Document chunking
│       └── llm.py            # LLM integration
├── documents/                # Folder dokumen (MD + original)
├── vector_db/                # FAISS index storage
├── .env                      # Environment config
├── requirements.txt          # Python dependencies
└── run.py                    # Alternative entry point
```

## � Menambah Dokumen

### Via Laravel Admin (Recommended)
1. Login ke SINEMA sebagai admin
2. Buka menu **Chatbot > Dokumen Chatbot**
3. Upload file (PDF/DOCX/TXT/MD)
4. Pilih kategori
5. Klik **Upload & Proses**

### Via API
```bash
curl -X POST http://127.0.0.1:5000/api/documents \
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
curl http://127.0.0.1:5000/api/stats
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

## 📝 License

Proyek skripsi - Fakultas Teknik Universitas Tadulako
