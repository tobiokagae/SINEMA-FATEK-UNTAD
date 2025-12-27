# SINEMA RAG Chatbot
## Fakultas Teknik - Universitas Tadulako

Sistem chatbot berbasis RAG (Retrieval-Augmented Generation) untuk menjawab pertanyaan seputar akademik.

### 📊 Status
- **Precision:** 83.3%
- **Success Rate:** 100%
- **Documents:** 5 (1429 chunks)

### 🚀 Fitur
- **RAG Pipeline** - Dokumen di-chunk dan di-embed untuk retrieval semantik
- **Query Rewriting** - LLM pahami pertanyaan sebelum search
- **Smart Cache** - Respons adaptif dari cache
- **LLM via API** - OpenRouter API (GPT-4o-mini)
- **FAISS Vector Store** - Penyimpanan embedding yang efisien
- **Streamlit UI** - Interface chat modern dengan dark theme
- **Multi-format** - Support PDF, DOCX, TXT, MD
- **Konversi Otomatis** - PDF/DOCX/TXT → Markdown
- **Conversation Context** - Ingat 6 pesan terakhir

### 📁 Knowledge Base
| Dokumen | Chunks |
|---------|--------|
| PANDUAN AKADEMIK FATEK 2025-2026 | 706 |
| Modul Integritas Akademik | 436 |
| Buku Panduan TA Non Skripsi | 216 |
| Panduan Poin Ekstrakurikuler | 65 |
| SINEMA Website Info | 6 |

### 🔧 Konfigurasi
| Parameter | Nilai |
|-----------|-------|
| Chunk Size | 400 karakter |
| Chunk Overlap | 100 karakter |
| Top-K | 25 |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 |

### ⚙️ Instalasi
```bash
cd sinema-chatbot
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### ▶️ Menjalankan
```bash
streamlit run streamlit_app.py
```
Buka browser: http://localhost:8501

### 📚 Menambah Dokumen
1. Buka halaman "📁 Dokumen" di UI
2. Upload file (PDF/DOCX/TXT/MD)
3. Pilih kategori
4. Klik "Upload & Proses"

### 🔧 Konfigurasi Environment
Edit `.env`:
```
OPENROUTER_API_KEY=your-api-key
USE_API=true
```

Edit `app/config.py` untuk:
- Chunk size
- Top-K retrieval
- System prompt
