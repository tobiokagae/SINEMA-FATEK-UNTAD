# -*- coding: utf-8 -*-
"""
Dashboard Evaluasi Expert - SINEMA RAG Chatbot
Instrumen validasi expert untuk menilai kualitas jawaban chatbot
Berdasarkan BAB II Bagian 2.6.3 - Expert Validation (Skala Likert 1-5)

Expert dapat langsung menguji chatbot dari dashboard ini, lalu menilai jawabannya.
"""

import streamlit as st
import json
import math
import re
import sys
import os
from datetime import datetime
from pathlib import Path

# =========================
# Project Setup
# =========================
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from app.config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, MODEL_DIR,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K,
    MAX_NEW_TOKENS, TEMPERATURE, TOP_P, DEVICE, SYSTEM_PROMPT,
    RELEVANCE_THRESHOLD
)
from app.rag import RAGRetriever

# Choose generator
USE_API = os.getenv('USE_API', 'false').lower() == 'true'
if USE_API:
    from app.llm.api_generator import APIGenerator as LLMGenerator
else:
    from app.llm import LLMGenerator

# =========================
# Configuration
# =========================
EVAL_DIR = PROJECT_ROOT / "evaluation"
EVAL_FILE = EVAL_DIR / "expert_evaluations.json"

ASPECTS = [
    {
        "key": "akurasi",
        "label": "Akurasi",
        "icon": "🎯",
        "indicator": "Jawaban sesuai dokumen resmi",
        "description": "Apakah jawaban chatbot sesuai dengan isi dokumen resmi yang menjadi knowledge base?"
    },
    {
        "key": "relevansi",
        "label": "Relevansi",
        "icon": "🔗",
        "indicator": "Jawaban sesuai pertanyaan",
        "description": "Apakah jawaban chatbot menjawab apa yang ditanyakan, bukan informasi yang tidak nyambung?"
    },
    {
        "key": "kelengkapan",
        "label": "Kelengkapan",
        "icon": "📋",
        "indicator": "Informasi penting tercakup",
        "description": "Apakah semua informasi penting yang relevan tercakup dalam jawaban?"
    },
    {
        "key": "kejelasan",
        "label": "Kejelasan",
        "icon": "💡",
        "indicator": "Mudah dipahami",
        "description": "Apakah jawaban mudah dipahami oleh mahasiswa?"
    },
]

LIKERT_LABELS = {
    1: "Sangat Buruk",
    2: "Buruk",
    3: "Cukup",
    4: "Baik",
    5: "Sangat Baik",
}

TARGET_SCORE = 4.0

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="Evaluasi Expert - SINEMA Chatbot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS
# =========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }

    .main { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }

    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem 2.5rem; border-radius: 20px; margin-bottom: 2rem;
        text-align: center; box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
        position: relative; overflow: hidden;
    }
    .hero-header::before {
        content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: pulse 4s ease-in-out infinite;
    }
    @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 0.8; } }
    .hero-header h1 { color: white; font-size: 2rem; font-weight: 800; margin: 0; position: relative; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .hero-header p { color: rgba(255,255,255,0.9); font-size: 1rem; margin: 0.5rem 0 0 0; position: relative; font-weight: 300; }

    .metric-card {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px;
        padding: 1.5rem; text-align: center; transition: all 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-4px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2); border-color: rgba(102, 126, 234, 0.4); }
    .metric-value { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2; }
    .metric-label { color: #a0aec0; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.5rem; }
    .metric-status { margin-top: 0.5rem; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .status-pass { background: rgba(72, 187, 120, 0.2); color: #48bb78; border: 1px solid rgba(72, 187, 120, 0.3); }
    .status-fail { background: rgba(245, 101, 101, 0.2); color: #f56565; border: 1px solid rgba(245, 101, 101, 0.3); }

    .aspect-card {
        background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;
        padding: 1.5rem; margin-bottom: 1rem; transition: all 0.3s ease;
    }
    .aspect-card:hover { border-color: rgba(102, 126, 234, 0.3); background: rgba(255, 255, 255, 0.06); }
    .aspect-title { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.3rem; }
    .aspect-indicator { font-size: 0.85rem; color: #a0aec0; margin-bottom: 0.75rem; font-style: italic; }

    .score-bar-container { background: rgba(255, 255, 255, 0.08); border-radius: 12px; height: 14px; overflow: hidden; margin-top: 0.5rem; }
    .score-bar { height: 100%; border-radius: 12px; transition: width 1s ease-in-out; }
    .score-bar.good { background: linear-gradient(90deg, #48bb78 0%, #38a169 100%); }
    .score-bar.warning { background: linear-gradient(90deg, #ecc94b 0%, #d69e2e 100%); }
    .score-bar.bad { background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%); }

    .chat-bubble-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0; max-width: 85%; margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .chat-bubble-bot {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
        border: 1px solid rgba(102, 126, 234, 0.2); color: #e2e8f0;
        padding: 1rem 1.5rem; border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0; max-width: 85%;
    }
    .chat-meta { color: #a0aec0; font-size: 0.8rem; margin-top: 0.3rem; }

    .eval-entry {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px; padding: 1.25rem; margin-bottom: 0.75rem; transition: all 0.3s ease;
    }
    .eval-entry:hover { border-color: rgba(102, 126, 234, 0.3); }
    .eval-question { color: #e2e8f0; font-weight: 600; font-size: 0.95rem; }
    .eval-scores { display: flex; gap: 0.75rem; margin-top: 0.5rem; flex-wrap: wrap; }
    .eval-score-badge { padding: 0.25rem 0.6rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; }

    .detail-table { width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 12px; overflow: hidden; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); }
    .detail-table th { background: rgba(102, 126, 234, 0.2); color: #e2e8f0; padding: 0.75rem 1rem; text-align: left; font-weight: 600; font-size: 0.85rem; }
    .detail-table td { color: #cbd5e0; padding: 0.75rem 1rem; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.85rem; }
    .detail-table tr:hover td { background: rgba(102, 126, 234, 0.05); }

    .score-high { color: #48bb78; font-weight: 700; }
    .score-med { color: #ecc94b; font-weight: 700; }
    .score-low { color: #f56565; font-weight: 700; }

    .target-line { display: flex; align-items: center; gap: 0.5rem; color: #a0aec0; font-size: 0.8rem; margin-top: 0.5rem; }
    .target-dot { width: 8px; height: 8px; background: #f56565; border-radius: 50%; }

    .stButton > button { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 0.6rem 2rem !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important; }
    .stTextArea textarea, .stTextInput input { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; color: #e2e8f0 !important; }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #667eea !important; box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important; }
    .stSelectbox > div > div { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }

    .section-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent); margin: 2rem 0; }
    .info-box { background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; padding: 1rem 1.25rem; border-radius: 0 12px 12px 0; margin: 1rem 0; color: #cbd5e0; font-size: 0.9rem; }
    .chart-container { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 1.5rem; }
    header[data-testid="stHeader"] { background: transparent; }

    .pending-eval-box {
        background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
        border: 2px solid rgba(102, 126, 234, 0.3); border-radius: 16px;
        padding: 1.5rem; margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# Load RAG Models (cached)
# =========================
def get_index_timestamp():
    index_path = VECTOR_DB_DIR / "index.faiss"
    if index_path.exists():
        return int(index_path.stat().st_mtime)
    return 0

@st.cache_resource(show_spinner=False)
def load_retriever(_index_timestamp: int):
    retriever = RAGRetriever(
        documents_dir=DOCUMENTS_DIR,
        vector_db_dir=VECTOR_DB_DIR,
        embedding_model_name=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD
    )
    retriever.initialize()
    return retriever

@st.cache_resource(show_spinner=False)
def load_generator():
    if USE_API:
        return LLMGenerator()
    else:
        gen = LLMGenerator(
            model_path=MODEL_DIR,
            device=DEVICE,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P
        )
        _ = gen.model
        return gen

# Preload at startup
with st.spinner("🚀 Memuat model AI (hanya sekali saat startup)..."):
    _retriever = load_retriever(get_index_timestamp())
    _generator = load_generator()


def ask_chatbot(question: str):
    """Send a question to the RAG chatbot and return (response, sources, latency).
    
    Pipeline 100% sama dengan routes.py production (Flask API / Laravel):
    1. Normalize text (collapse repeated letters)
    2. Greeting/identity detection → direct LLM with SYSTEM_PROMPT
    3. RAG: retriever.get_context(query) → early return if empty → generator.generate()
    4. Source filtering: score > 0.4, top 1 only
    """
    import time as _time

    retriever = load_retriever(get_index_timestamp())
    generator = load_generator()

    total_start = _time.time()

    print(f"\n{'='*60}")
    print(f"📨 PERTANYAAN: {question[:80]}{'...' if len(question)>80 else ''}")
    print(f"{'='*60}")

    # ─── Greeting/Identity Detection (SAME AS routes.py) ───
    # Normalize repeated letters (haiiii → hai, halooo → halo)
    def normalize_text(text):
        return re.sub(r'(.)\1{2,}', r'\1', text.lower().strip())

    query_normalized = normalize_text(question)

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

    if is_simple_query:
        print(f"🏷️  Klasifikasi: DIRECT (greeting/identity — skip RAG)")
        gen_start = _time.time()
        # SAME AS routes.py: uses SYSTEM_PROMPT, not custom greeting prompt
        response, latency = generator.generate(
            query=question,
            context="",
            system_prompt=SYSTEM_PROMPT
        )
        gen_time = _time.time() - gen_start
        total_time = _time.time() - total_start
        print(f"⚡ LLM Generate : {gen_time:.2f}s (API latency: {latency:.2f}s)")
        print(f"✅ TOTAL        : {total_time:.2f}s")
        print(f"{'='*60}\n")
        return response, [], latency

    # ─── RAG Pipeline (SAME AS routes.py) ───
    print(f"🏷️  Klasifikasi: RAG PIPELINE")

    # Step 1: Get RAG context (SAME: retriever.get_context(query))
    ret_start = _time.time()
    context = retriever.get_context(question)
    ret_time = _time.time() - ret_start
    print(f"1️⃣  Retrieval    : {ret_time:.2f}s")
    print(f"   Context length: {len(context)} chars")

    # Early return if no relevant documents found (prevent hallucination)
    # SAME AS routes.py: context < 50 chars → reject
    if not context or len(context.strip()) < 50:
        total_time = _time.time() - total_start
        print(f"⚠️  Context terlalu pendek/kosong — menolak menjawab")
        print(f"✅ TOTAL        : {total_time:.2f}s")
        print(f"{'='*60}\n")
        no_info = "Maaf, saya tidak menemukan informasi yang relevan tentang pertanyaan Anda dalam dokumen. Silakan coba pertanyaan lain atau hubungi admin FATEK untuk informasi lebih lanjut. 😊"
        return no_info, [], 0.0

    # Get sources (SAME AS routes.py: score > 0.4, top 1 only)
    results = retriever.retrieve(question)
    sources = [
        {
            'source': doc.metadata.get('source', 'unknown'),
            'heading': doc.metadata.get('heading', ''),
            'snippet': doc.metadata.get('snippet', '')
        }
        for doc, score in results
        if score > 0.4  # Only include relevant sources
    ][:1]  # Limit to top 1 only
    if sources:
        print(f"   Source: {sources[0]['source']} (score > 0.4)")
    else:
        print(f"   No sources with score > 0.4")

    # Step 2: Generate response (SAME AS routes.py)
    gen_start = _time.time()
    response, latency = generator.generate(
        query=question,
        context=context,
        system_prompt=SYSTEM_PROMPT
    )
    gen_time = _time.time() - gen_start

    # Clean HTML
    response = re.sub(r'<[^>]+>', '', response)

    total_time = _time.time() - total_start
    print(f"2️⃣  LLM Generate : {gen_time:.2f}s (API latency: {latency:.2f}s)")
    print(f"   Response length: {len(response)} chars")
    print(f"{'─'*60}")
    print(f"✅ TOTAL         : {total_time:.2f}s")
    print(f"   ├─ Retrieval  : {ret_time:.2f}s ({ret_time/total_time*100:.0f}%)")
    print(f"   └─ Generate   : {gen_time:.2f}s ({gen_time/total_time*100:.0f}%)")
    print(f"{'='*60}\n")

    return response, sources, latency


# =========================
# Data Management
# =========================
def load_evaluations():
    if EVAL_FILE.exists():
        try:
            with open(EVAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {"evaluations": [], "metadata": {}}
    return {"evaluations": [], "metadata": {}}


def save_evaluations(data):
    EVAL_DIR.mkdir(exist_ok=True)
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    data["metadata"]["total_evaluations"] = len(data["evaluations"])
    with open(EVAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_csv(data):
    lines = ["No,Expert,Kategori,Pertanyaan,Jawaban Chatbot,Akurasi,Relevansi,Kelengkapan,Kejelasan,Rata-rata,Komentar,Waktu"]
    for i, ev in enumerate(data["evaluations"], 1):
        scores = ev["scores"]
        avg = sum(scores.values()) / len(scores)
        comment = ev.get("comment", "").replace(",", ";").replace("\n", " ")
        answer = ev.get("answer", "").replace(",", ";").replace("\n", " ")
        question = ev["question"].replace(",", ";").replace("\n", " ")
        lines.append(
            f'{i},{ev.get("expert_name", "-")},{ev.get("category", "-")},'
            f'"{question}","{answer}",'
            f'{scores["akurasi"]},{scores["relevansi"]},'
            f'{scores["kelengkapan"]},{scores["kejelasan"]},'
            f'{avg:.2f},"{comment}",{ev["timestamp"]}'
        )
    return "\n".join(lines)


# =========================
# Visualization Helpers
# =========================
def score_color_class(score):
    if score >= 4.0: return "good"
    elif score >= 3.0: return "warning"
    return "bad"

def score_css_class(score):
    if score >= 4.0: return "score-high"
    elif score >= 3.0: return "score-med"
    return "score-low"

def _score_hex(score):
    if score >= 4.0: return "#48bb78"
    elif score >= 3.0: return "#ecc94b"
    elif score > 0: return "#f56565"
    return "#a0aec0"

def render_score_bar(score, max_score=5):
    pct = (score / max_score) * 100
    color_class = score_color_class(score)
    return f'<div class="score-bar-container"><div class="score-bar {color_class}" style="width: {pct}%"></div></div>'

def render_radar_svg(averages, size=300):
    cx, cy = size / 2, size / 2
    r = size * 0.35
    n = len(ASPECTS)
    labels = [a["label"] for a in ASPECTS]
    values = [averages.get(a["key"], 0) for a in ASPECTS]

    def polar(angle_deg, radius):
        rad = math.radians(angle_deg - 90)
        return cx + radius * math.cos(rad), cy + radius * math.sin(rad)

    angles = [i * (360 / n) for i in range(n)]

    grid = ""
    for lv in [1,2,3,4,5]:
        pts = " ".join(f"{polar(a, r*lv/5)[0]},{polar(a, r*lv/5)[1]}" for a in angles)
        grid += f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>\n'

    axes = "".join(f'<line x1="{cx}" y1="{cy}" x2="{polar(a,r)[0]}" y2="{polar(a,r)[1]}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>' for a in angles)

    data_pts = " ".join(f"{polar(angles[i], r*values[i]/5)[0]},{polar(angles[i], r*values[i]/5)[1]}" for i in range(n))
    data_poly = f'<polygon points="{data_pts}" fill="rgba(102,126,234,0.25)" stroke="#667eea" stroke-width="2.5"/>'
    dots = "".join(f'<circle cx="{polar(angles[i], r*values[i]/5)[0]}" cy="{polar(angles[i], r*values[i]/5)[1]}" r="5" fill="#667eea" stroke="white" stroke-width="2"/>' for i in range(n))

    target_pts = " ".join(f"{polar(a, r*TARGET_SCORE/5)[0]},{polar(a, r*TARGET_SCORE/5)[1]}" for a in angles)
    target_poly = f'<polygon points="{target_pts}" fill="none" stroke="#f56565" stroke-width="1.5" stroke-dasharray="6,4"/>'

    label_elems = ""
    for i, lbl in enumerate(labels):
        lx, ly = polar(angles[i], r + 30)
        v = values[i]
        label_elems += f'<text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" fill="#a0aec0" font-size="13" font-weight="600">{lbl}</text>'
        label_elems += f'<text x="{lx}" y="{ly+16}" text-anchor="middle" dominant-baseline="middle" fill="{_score_hex(v)}" font-size="12" font-weight="700">{v:.1f}</text>'

    return f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;margin:auto;display:block;">{grid}{axes}{target_poly}{data_poly}{dots}{label_elems}</svg>'


def render_gauge(score, label="Rata-rata", size=200):
    cx, cy = size / 2, size * 0.6
    r = size * 0.38
    pct = min(score / 5, 1.0)
    color = _score_hex(score)

    def arc(angle_deg):
        rad = math.radians(angle_deg)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)

    sx, sy = arc(180)
    end_angle = 180 - (pct * 180)
    ex, ey = arc(end_angle)
    large = 1 if pct > 0.5 else 0
    tx, ty = arc(180 - (TARGET_SCORE / 5 * 180))

    bg_ex, bg_ey = arc(0)
    return f"""<svg viewBox="0 0 {size} {size*0.7}" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;margin:auto;display:block;">
    <path d="M {sx} {sy} A {r} {r} 0 1 1 {bg_ex} {bg_ey}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="12" stroke-linecap="round"/>
    <path d="M {sx} {sy} A {r} {r} 0 {large} 1 {ex} {ey}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
    <circle cx="{tx}" cy="{ty}" r="5" fill="#f56565" stroke="white" stroke-width="2"/>
    <text x="{cx}" y="{cy-8}" text-anchor="middle" fill="{color}" font-size="32" font-weight="800">{score:.2f}</text>
    <text x="{cx}" y="{cy+14}" text-anchor="middle" fill="#a0aec0" font-size="11" font-weight="500">{label}</text>
    <circle cx="{cx-40}" cy="{cy+32}" r="4" fill="#f56565"/>
    <text x="{cx-32}" y="{cy+36}" fill="#a0aec0" font-size="10">Target ≥{TARGET_SCORE}</text>
    </svg>"""


# =========================
# Session State
# =========================
if 'eval_data' not in st.session_state:
    st.session_state.eval_data = load_evaluations()
if 'pending_response' not in st.session_state:
    st.session_state.pending_response = None  # {'question':..., 'answer':..., 'sources':..., 'latency':...}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []  # For display in chat tab

data = st.session_state.eval_data


# =========================
# Header
# =========================
st.markdown("""
<div class="hero-header">
    <h1>📊 Dashboard Evaluasi Expert</h1>
    <p>Uji chatbot langsung & nilai jawabannya — Skala Likert 1-5 · SINEMA RAG Chatbot</p>
</div>
""", unsafe_allow_html=True)


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("### 📊 Evaluasi Expert")
    st.markdown("---")
    page = st.radio(
        "📍 Navigasi",
        ["🤖 Uji Chatbot", "📈 Dashboard", "📋 Detail Data"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("### ℹ️ Panduan Skor")
    for val, lbl in LIKERT_LABELS.items():
        emoji = "🟢" if val >= 4 else ("🟡" if val >= 3 else "🔴")
        st.markdown(f"{emoji} **{val}** — {lbl}")
    st.markdown("---")
    st.markdown(f"**Target:** ≥ {TARGET_SCORE} per aspek")
    st.markdown(f"**Total Evaluasi:** {len(data['evaluations'])}")
    st.markdown("---")
    if data["evaluations"]:
        csv = export_csv(data)
        st.download_button("📥 Ekspor CSV", csv,
            file_name=f"expert_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv")


# =================================================================
# Page: 🤖 Uji Chatbot  (Test + Evaluate in one flow)
# =================================================================
if page == "🤖 Uji Chatbot":

    st.markdown("""
    <div class="info-box">
        <strong>Alur:</strong> (1) Masukkan pertanyaan → (2) Chatbot menjawab secara langsung → (3) Berikan skor evaluasi.<br>
        Sesuai instrumen <strong>Tabel 8 BAB II (2.6.3)</strong>.
    </div>
    """, unsafe_allow_html=True)

    # --- Expert info (persisted in session) ---
    if 'expert_name' not in st.session_state:
        st.session_state.expert_name = ""
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.session_state.expert_name = st.text_input(
            "👤 Nama Expert / Evaluator",
            value=st.session_state.expert_name,
            placeholder="Contoh: Staff Bag. Kemahasiswaan"
        )
    with col_e2:
        eval_category = st.selectbox("📂 Kategori Pertanyaan", [
            "Panduan Ekstrakurikuler", "Panduan Akademik", "Panduan TA",
            "Integritas Akademik", "SINEMA", "Lainnya"
        ])

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Chat History Display ---
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown('<div class="chat-bubble-bot">', unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg.get("sources"):
                    src_list = ", ".join(s['source'] for s in msg['sources'][:3])
                    st.caption(f"📚 Sumber: {src_list}")
                st.markdown('</div>', unsafe_allow_html=True)
            if msg.get("latency") and msg["latency"] > 0:
                st.caption(f"⚡ Response time: {msg['latency']:.2f}s")

    st.markdown("---")

    # --- Question Input ---
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        user_question = st.text_input(
            "❓ Ketik pertanyaan untuk chatbot...",
            placeholder="Contoh: Berapa poin minimal ekstrakurikuler yang harus dikumpulkan?",
            label_visibility="collapsed",
            key=f"q_input_{len(st.session_state.chat_history)}"
        )
    with col_btn:
        send_btn = st.button("Kirim 📤", use_container_width=True)

    # --- Suggested questions ---
    if not st.session_state.chat_history:
        st.markdown("**💡 Contoh pertanyaan:**")
        suggestions = [
            "📚 Apa syarat untuk mengambil Tugas Akhir?",
            "🌐 Bagaimana cara mendapatkan poin SINEMA?",
            "⚖️ Apa sanksi plagiarisme?",
        ]
        cols = st.columns(3)
        for i, sq in enumerate(suggestions):
            with cols[i]:
                if st.button(sq, key=f"sug_{i}", use_container_width=True):
                    st.session_state._suggested_q = sq.split(" ", 1)[1]
                    st.rerun()

    # Handle suggested question
    if '_suggested_q' in st.session_state and st.session_state._suggested_q:
        user_question = st.session_state._suggested_q
        st.session_state._suggested_q = None
        send_btn = True

    # --- Process question ---
    if send_btn and user_question and user_question.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_question.strip()})

        with st.spinner("🤔 Chatbot sedang berpikir..."):
            try:
                response, sources, latency = ask_chatbot(user_question.strip())
                st.session_state.chat_history.append({
                    "role": "assistant", "content": response,
                    "sources": sources, "latency": latency
                })
                st.session_state.pending_response = {
                    "question": user_question.strip(),
                    "answer": response,
                    "sources": sources,
                    "latency": latency
                }
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.pending_response = None

        st.rerun()

    # --- Evaluation Form (appears after chatbot responds) ---
    if st.session_state.pending_response:
        pr = st.session_state.pending_response
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="pending-eval-box">
            <h4 style="color: #e2e8f0; margin: 0 0 0.5rem 0;">📝 Berikan Penilaian untuk Jawaban Terakhir</h4>
            <p style="color: #a0aec0; margin: 0; font-size: 0.9rem;">Nilai kualitas jawaban chatbot di atas berdasarkan 4 aspek berikut.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("eval_form", clear_on_submit=False):
            scores = {}
            for i in range(0, len(ASPECTS), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(ASPECTS):
                        aspect = ASPECTS[i + j]
                        with col:
                            st.markdown(f"""
                            <div class="aspect-card">
                                <div class="aspect-title">{aspect['icon']} {aspect['label']}</div>
                                <div class="aspect-indicator">{aspect['indicator']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            scores[aspect['key']] = st.slider(
                                f"{aspect['label']}", 1, 5, 3,
                                help=aspect['description'], label_visibility="collapsed"
                            )

            comment = st.text_area("💬 Komentar (opsional)", placeholder="Catatan tambahan...", height=60)

            col_submit, col_skip = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("✅ Simpan Evaluasi", use_container_width=True)
            with col_skip:
                skipped = st.form_submit_button("⏭️ Lewati (Tidak Dinilai)", use_container_width=True)

            if submitted:
                ev = {
                    "id": len(data["evaluations"]) + 1,
                    "expert_name": st.session_state.expert_name.strip() or "Anonymous",
                    "category": eval_category,
                    "question": pr["question"],
                    "answer": pr["answer"],
                    "sources": [s['source'] for s in pr.get("sources", [])[:3]],
                    "latency": pr.get("latency", 0),
                    "scores": scores,
                    "comment": comment.strip(),
                    "timestamp": datetime.now().isoformat()
                }
                data["evaluations"].append(ev)
                save_evaluations(data)
                st.session_state.eval_data = data
                st.session_state.pending_response = None
                avg = sum(scores.values()) / len(scores)
                if avg >= TARGET_SCORE:
                    st.balloons()
                st.rerun()

            if skipped:
                st.session_state.pending_response = None
                st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Hapus Riwayat Chat", use_container_width=False):
            st.session_state.chat_history = []
            st.session_state.pending_response = None
            st.rerun()


# =================================================================
# Page: 📈 Dashboard
# =================================================================
elif page == "📈 Dashboard":
    evaluations = data["evaluations"]

    if not evaluations:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;">
            <p style="font-size:4rem;">📭</p>
            <h3 style="color:#a0aec0;">Belum Ada Data Evaluasi</h3>
            <p style="color:#718096;">Uji chatbot di menu "🤖 Uji Chatbot" lalu berikan penilaian.</p>
        </div>""", unsafe_allow_html=True)
    else:
        n = len(evaluations)
        aspect_sums = {a["key"]: 0 for a in ASPECTS}
        for ev in evaluations:
            for k in aspect_sums:
                aspect_sums[k] += ev["scores"].get(k, 0)
        aspect_avgs = {k: v / n for k, v in aspect_sums.items()}
        overall_avg = sum(aspect_avgs.values()) / len(aspect_avgs)

        # --- Top Metrics ---
        cols = st.columns(5)
        items = [("Total Evaluasi", f"{n}", None)]
        for a in ASPECTS:
            avg = aspect_avgs[a["key"]]
            items.append((a["label"], f"{avg:.2f}", "pass" if avg >= TARGET_SCORE else "fail"))
        for col, (label, value, status) in zip(cols, items):
            with col:
                s_html = ""
                if status == "pass": s_html = '<div class="metric-status status-pass">✓ Memenuhi Target</div>'
                elif status == "fail": s_html = '<div class="metric-status status-fail">✗ Di Bawah Target</div>'
                st.markdown(f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div>{s_html}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # --- Charts ---
        col_r, col_g = st.columns([3, 2])
        with col_r:
            st.markdown("#### 🕸️ Radar Chart — Rata-rata per Aspek")
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(render_radar_svg(aspect_avgs, 320), unsafe_allow_html=True)
            st.markdown('<div class="target-line"><div class="target-dot"></div>Garis putus-putus merah = Target ≥4.0</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_g:
            st.markdown("#### 🎯 Skor Keseluruhan")
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(render_gauge(overall_avg, "Rata-rata Keseluruhan", 260), unsafe_allow_html=True)
            if overall_avg >= TARGET_SCORE:
                st.markdown('<div style="text-align:center;margin-top:1rem;"><span class="metric-status status-pass" style="font-size:1rem;padding:0.5rem 1.5rem;">✅ LULUS — Memenuhi Target</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center;margin-top:1rem;"><span class="metric-status status-fail" style="font-size:1rem;padding:0.5rem 1.5rem;">❌ BELUM LULUS — Perlu Perbaikan</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # --- Aspect Bars ---
        st.markdown("#### 📊 Detail Skor per Aspek")
        for aspect in ASPECTS:
            avg = aspect_avgs[aspect["key"]]
            css = score_css_class(avg)
            status = "✓ Memenuhi" if avg >= TARGET_SCORE else "✗ Belum"
            st.markdown(f"""
            <div class="aspect-card"><div style="display:flex;justify-content:space-between;align-items:center;">
                <div><div class="aspect-title">{aspect['icon']} {aspect['label']}</div><div class="aspect-indicator">{aspect['indicator']}</div></div>
                <div style="text-align:right;"><span class="{css}" style="font-size:1.8rem;">{avg:.2f}</span><span style="color:#a0aec0;font-size:0.8rem;"> / 5.00</span></div>
            </div>{render_score_bar(avg)}<div class="target-line"><div class="target-dot"></div>Target: ≥{TARGET_SCORE} | Status: {status}</div></div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # --- Per-question scores ---
        st.markdown("#### 📝 Skor per Pertanyaan")
        for i, ev in enumerate(evaluations):
            sc = ev["scores"]
            avg = sum(sc.values()) / len(sc)
            q_short = ev["question"][:80] + ("..." if len(ev["question"]) > 80 else "")
            badges = "".join(f'<span class="eval-score-badge" style="background:{_score_hex(sc[a["key"]])}22;color:{_score_hex(sc[a["key"]])};border:1px solid {_score_hex(sc[a["key"]])}44;">{a["icon"]} {sc[a["key"]]}</span>' for a in ASPECTS)
            st.markdown(f"""
            <div class="eval-entry"><div style="display:flex;justify-content:space-between;align-items:start;">
                <div class="eval-question">#{i+1}. {q_short}</div>
                <span class="{score_css_class(avg)}" style="font-size:1.2rem;font-weight:700;">{avg:.1f}</span>
            </div><div class="eval-scores">{badges}</div></div>
            """, unsafe_allow_html=True)


# =================================================================
# Page: 📋 Detail Data
# =================================================================
elif page == "📋 Detail Data":
    evaluations = data["evaluations"]

    if not evaluations:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;">
            <p style="font-size:4rem;">📭</p>
            <h3 style="color:#a0aec0;">Belum Ada Data Evaluasi</h3>
            <p style="color:#718096;">Uji chatbot di menu "🤖 Uji Chatbot" lalu berikan penilaian.</p>
        </div>""", unsafe_allow_html=True)
    else:
        n = len(evaluations)
        st.markdown("#### 📋 Tabel Detail Evaluasi")

        total_scores = {a["key"]: 0 for a in ASPECTS}
        rows = ""
        for i, ev in enumerate(evaluations, 1):
            sc = ev["scores"]
            avg = sum(sc.values()) / len(sc)
            cells = ""
            for a in ASPECTS:
                s = sc[a["key"]]
                total_scores[a["key"]] += s
                cells += f'<td class="{score_css_class(s)}">{s}</td>'
            ts = datetime.fromisoformat(ev["timestamp"]).strftime("%d/%m/%Y %H:%M")
            q_short = ev["question"][:60] + ("..." if len(ev["question"]) > 60 else "")
            rows += f'<tr><td>{i}</td><td>{ev.get("expert_name","-")}</td><td>{q_short}</td>{cells}<td class="{score_css_class(avg)}">{avg:.2f}</td><td>{ts}</td></tr>'

        footer_cells = ""
        for a in ASPECTS:
            tavg = total_scores[a["key"]] / n
            footer_cells += f'<td class="{score_css_class(tavg)}" style="font-weight:700;">{tavg:.2f}</td>'
        overall = sum(total_scores.values()) / (n * len(ASPECTS))

        st.markdown(f"""
        <div style="overflow-x:auto;">
        <table class="detail-table">
        <thead><tr><th>No</th><th>Expert</th><th>Pertanyaan</th><th>🎯</th><th>🔗</th><th>📋</th><th>💡</th><th>Avg</th><th>Waktu</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr style="background:rgba(102,126,234,0.1);"><td colspan="3" style="font-weight:700;">📊 RATA-RATA</td>{footer_cells}<td class="{score_css_class(overall)}" style="font-weight:700;">{overall:.2f}</td><td>—</td></tr></tfoot>
        </table></div>
        """, unsafe_allow_html=True)

        # Target comparison
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 🎯 Perbandingan dengan Target")
        target_rows = ""
        all_pass = True
        for a in ASPECTS:
            tavg = total_scores[a["key"]] / n
            status = "✅ LULUS" if tavg >= TARGET_SCORE else "❌ BELUM"
            if tavg < TARGET_SCORE: all_pass = False
            diff = tavg - TARGET_SCORE
            d_sign = "+" if diff >= 0 else ""
            d_color = "#48bb78" if diff >= 0 else "#f56565"
            target_rows += f'<tr><td>{a["icon"]} {a["label"]}</td><td>{a["indicator"]}</td><td>≥ {TARGET_SCORE}</td><td class="{score_css_class(tavg)}">{tavg:.2f}</td><td style="color:{d_color};font-weight:700;">{d_sign}{diff:.2f}</td><td>{status}</td></tr>'

        st.markdown(f"""<table class="detail-table">
        <thead><tr><th>Aspek</th><th>Indikator</th><th>Target</th><th>Hasil</th><th>Selisih</th><th>Status</th></tr></thead>
        <tbody>{target_rows}</tbody></table>""", unsafe_allow_html=True)

        if all_pass:
            st.success("🎉 Semua aspek memenuhi target validasi expert!")
        else:
            st.warning("⚠️ Ada aspek yang belum memenuhi target. Perlu perbaikan sebelum sistem dianggap siap.")

        # Comments
        comments = [(ev.get("expert_name","-"), ev["question"][:50], ev.get("comment",""))
                     for ev in evaluations if ev.get("comment","").strip()]
        if comments:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("#### 💬 Komentar Expert")
            for name, q, c in comments:
                st.markdown(f"""<div class="eval-entry">
                <div style="color:#667eea;font-weight:600;font-size:0.85rem;">👤 {name}</div>
                <div style="color:#a0aec0;font-size:0.8rem;margin-bottom:0.5rem;">Re: {q}...</div>
                <div style="color:#e2e8f0;font-size:0.9rem;">"{c}"</div></div>""", unsafe_allow_html=True)

        # Danger zone
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        with st.expander("⚠️ Zona Bahaya"):
            st.warning("Tindakan di bawah ini tidak dapat dibatalkan!")
            if st.button("🗑️ Hapus Semua Data Evaluasi", type="secondary"):
                data["evaluations"] = []
                save_evaluations(data)
                st.session_state.eval_data = data
                st.rerun()
