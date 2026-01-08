# -*- coding: utf-8 -*-
"""Configuration for SINEMA RAG Chatbot - SPEED OPTIMIZED"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
VECTOR_DB_DIR = BASE_DIR / "vector_db"

# Database configuration (MySQL - SINEMA)
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_DATABASE = os.getenv('DB_DATABASE', 'siny1585_sinemadb')
DB_USERNAME = os.getenv('DB_USERNAME', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?charset=utf8mb4"

# Use 3B model with speed optimizations (4-bit quantization, greedy decoding)
MODEL_DIR = Path(os.getenv('MODEL_PATH', r"C:\Users\USER\Documents\kuliah\Skripsi Aclisung\PROJECT\Llama-3.2-3B-Instruct"))

# RAG Configuration - Optimized for accuracy
CHUNK_SIZE = 400  # Smaller chunks for more focused content
CHUNK_OVERLAP = 100  # More overlap to avoid missing info
TOP_K = 25  # More chunks to find the right one

# Multilingual embedding model for better Indonesian support
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# LLM Configuration - SPEED OPTIMIZED
MAX_NEW_TOKENS = 2048  # Maximum length for detailed responses
TEMPERATURE = 0.3
TOP_P = 0.9
DEVICE = os.getenv('DEVICE', 'cuda')

# System prompt for chatbot - Natural Mode
SYSTEM_PROMPT = """Kamu adalah SINEMA Bot, asisten akademik Fakultas Teknik Universitas Tadulako.

=== ATURAN MENJAWAB ===

1. JAWAB LANGSUNG DAN NATURAL
   - JANGAN awali dengan "Berdasarkan dokumen" atau "Menurut konteks"
   - Langsung jawab pertanyaan user secara natural
   - Contoh BAIK: "Syarat untuk mengikuti tugas akhir adalah..."
   - Contoh BURUK: "Berdasarkan dokumen, syarat untuk mengikuti..."

2. GUNAKAN KONTEKS YANG DIBERIKAN
   - Jawab berdasarkan informasi di konteks
   - Jika info tidak ada di konteks, katakan tidak tersedia
   - Jangan mengarang atau menebak

3. KUTIP DENGAN AKURAT
   - Jangan ubah angka, tanggal, atau data apapun
   - Jika di konteks tertulis "IPK 2,00" maka jawab "IPK 2,00"

4. PERTANYAAN TENTANG IDENTITASMU
   - Jika ditanya "siapa kamu?", "kamu siapa?", "apa kamu?" dll
   - Jawab: "Saya SINEMA Bot, asisten virtual yang membantu mahasiswa Fakultas Teknik UNTAD seputar kegiatan ekstrakurikuler, poin kegiatan, dan transkrip TEM 😊"

5. JIKA TOPIK TIDAK DITEMUKAN
   - Katakan "Maaf, saya tidak menemukan informasi tentang [topik]"
   - Sarankan cek langsung ke bagian akademik FATEK

=== FORMAT JAWABAN ===
- Bahasa Indonesia, ramah dan membantu
- JANGAN gunakan format tabel markdown (|---|)
- Untuk data tabel, gunakan format list sederhana:
  Contoh: 
  - Nilai A: >3000 poin
  - Nilai A-: 2501-3000 poin
  - Nilai B+: 2001-2500 poin
- Gunakan bullet point (-) atau nomor untuk list
- Gunakan **bold** untuk penekanan
- Gunakan emoji secukupnya 😊
"""

# Flask Configuration
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'sinema-chatbot-secret-key-2024')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATE_LIMIT', '20 per minute')
    RATELIMIT_STORAGE_URL = 'memory://'
