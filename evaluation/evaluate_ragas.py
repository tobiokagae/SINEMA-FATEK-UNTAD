# -*- coding: utf-8 -*-
"""
Evaluasi RAGAS - SINEMA RAG Chatbot
Script untuk mengevaluasi performa RAG menggunakan framework RAGAS
Sesuai BAB II: Context Precision, Context Recall, Faithfulness, Answer Relevancy

Output: evaluation/ragas_results.json → mengisi Tabel 15-19 BAB III

Cara menjalankan:
    cd d:\\Skripsi\\Andi Alisha Faiqihah\\sinema\\backend
    python evaluation/evaluate_ragas.py
"""

import sys
import json
import time
import os
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path (backend/ is parent of evaluation/)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from app.rag.retriever import RAGRetriever
from app.llm.api_generator import APIGenerator
from app.config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, SYSTEM_PROMPT
)

# ============================================================
# Configuration
# ============================================================
BENCHMARK_FILE = PROJECT_ROOT / "evaluation" / "benchmark_dataset.json"
OUTPUT_FILE = PROJECT_ROOT / "evaluation" / "ragas_results.json"
CACHE_FILE = PROJECT_ROOT / "evaluation" / "collected_cache.json"

# Markers that indicate an error/rate-limited response (not a real answer)
ERROR_MARKERS = [
    "Semua API key sudah mencapai batas limit",
    "Rate limit exceeded",
    "API key sudah mencapai batas",
]

# RAGAS target metrics (from BAB II)
TARGETS = {
    "context_precision": 0.80,
    "context_recall": 0.85,
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
}

# Category display names
CATEGORY_NAMES = {
    "panduan_akademik": "Panduan Akademik",
    "poin_ekstrakurikuler": "Poin Ekstrakurikuler",
    "ta_skripsi": "TA/Skripsi",
    "integritas_akademik": "Integritas Akademik",
    "website_sinema": "Website SINEMA",
}


# ============================================================
# Helper Functions
# ============================================================
def load_benchmark_dataset():
    """Load benchmark dataset from JSON file"""
    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["questions"]


def _is_error_answer(answer):
    """Check if an answer is a rate-limit error message, not a real response."""
    if not answer:
        return True
    for marker in ERROR_MARKERS:
        if marker in answer:
            return True
    return False


def _load_cache():
    """Load cached collected responses if available."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("responses", [])
        except (json.JSONDecodeError, KeyError):
            return []
    return []


def _save_cache(collected_results):
    """Save collected responses to cache file (full data including contexts)."""
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "total": len(collected_results),
        "valid": sum(1 for r in collected_results if not _is_error_answer(r["answer"])),
        "error": sum(1 for r in collected_results if _is_error_answer(r["answer"])),
        "responses": collected_results,
    }
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"   💾 Cache disimpan ke: {CACHE_FILE.name}")


def collect_rag_responses(retriever, generator, questions, cached_results=None):
    """
    Run RAG pipeline for each question and collect responses + contexts.
    Supports resuming from cached results - skips questions with valid cached answers.

    Returns list of dicts with: question, answer, contexts, ground_truth,
    category, retrieval_latency, generation_latency, total_latency, avg_score
    """
    # Build lookup of valid cached results by question id
    cache_map = {}
    if cached_results:
        for r in cached_results:
            if not _is_error_answer(r.get("answer", "")):
                cache_map[r["id"]] = r

    results = []
    total = len(questions)
    skipped = 0
    collected = 0
    errors = 0

    for i, item in enumerate(questions, 1):
        qid = item["id"]
        question = item["question"]
        ground_truth = item["ground_truth"]
        category = item["category"]

        # Check cache for valid answer
        if qid in cache_map:
            cached = cache_map[qid]
            results.append(cached)
            skipped += 1
            print(f"  [{i:2d}/{total}] ⏩ CACHED: {question[:55]}...")
            continue

        print(f"  [{i:2d}/{total}] {question[:60]}...")

        # --- Retrieval ---
        t0 = time.time()
        retrieval_results = retriever.retrieve(question)
        retrieval_latency = time.time() - t0

        # Extract contexts and scores
        contexts = []
        scores = []
        for doc, score in retrieval_results[:TOP_K]:
            contexts.append(doc.page_content)
            scores.append(float(score))

        avg_score = sum(scores) / len(scores) if scores else 0.0

        # --- Generation ---
        context_text = "\n\n".join(contexts)
        t1 = time.time()
        answer, _ = generator.generate(
            query=question,
            context=context_text,
            system_prompt=SYSTEM_PROMPT,
            conversation_history=[]
        )
        generation_latency = time.time() - t1
        total_latency = retrieval_latency + generation_latency

        result_entry = {
            "id": qid,
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth,
            "category": category,
            "retrieval_latency": round(retrieval_latency, 4),
            "generation_latency": round(generation_latency, 4),
            "total_latency": round(total_latency, 4),
            "avg_score": round(avg_score, 4),
        }
        results.append(result_entry)

        if _is_error_answer(answer):
            errors += 1
            print(f"       ❌ Error response (rate limit?)")
        else:
            collected += 1
            status = "✅" if avg_score > 0.3 else "⚠️"
            print(f"       {status} Score: {avg_score:.3f} | Latency: {total_latency:.2f}s")

        # Save cache after each question (so we don't lose progress)
        _save_cache(results)

    print(f"\n   📊 Ringkasan: {skipped} dari cache, {collected} baru, {errors} error")
    return results


# def _load_api_keys():
#     """
#     Load all available OpenRouter API keys.
#     Supports OPENROUTER_API_KEYS (comma-separated) and fallback OPENROUTER_API_KEY.
#     """
#     keys = []
#     keys_str = os.getenv("OPENROUTER_API_KEYS", "")
#     if keys_str:
#         keys = [k.strip() for k in keys_str.split(",") if k.strip()]
#     if not keys:
#         single_key = os.getenv("OPENROUTER_API_KEY", "")
#         if single_key:
#             keys = [single_key]
#     return keys


# class _RotatingKeyManager:
#     """Thread-safe API key rotation manager."""
#     def __init__(self, keys):
#         self.keys = keys
#         self.index = 0
#         self.lock = threading.Lock()
#         self.call_count = 0

#     def get_key(self):
#         with self.lock:
#             key = self.keys[self.index]
#             self.call_count += 1
#             # Rotate to next key every N calls to spread load
#             if self.call_count % 3 == 0:
#                 self.index = (self.index + 1) % len(self.keys)
#             return key

#     def force_rotate(self):
#         with self.lock:
#             self.index = (self.index + 1) % len(self.keys)
#             return self.keys[self.index]

#     def set_key_index(self, idx):
#         with self.lock:
#             self.index = idx % len(self.keys)


# Global key manager (initialized in _setup_ragas_llm)
_key_manager = None


def _setup_ragas_llm():
    """
    Konfigurasi LLM Gemini sebagai evaluator RAGAS.
    Menggunakan gemini-2.0-flash untuk kuota lebih besar.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY tidak ditemukan di .env!")
            return None, None

        # LLM Gemini sebagai Hakim - pakai gemini-2.0-flash (kuota besar)
        gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0
        )
        ragas_llm = LangchainLLMWrapper(gemini_llm)

        # Google Embeddings untuk Answer Relevancy
        gemini_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-004",
            google_api_key=api_key
        )
        ragas_emb = LangchainEmbeddingsWrapper(gemini_embeddings)

        print(f"   ✅ RAGAS LLM (gemini-2.0-flash) & Embeddings dikonfigurasi")
        return ragas_llm, ragas_emb

    except Exception as e:
        print(f"   ❌ Gagal konfigurasi Gemini: {e}")
        return None, None


PROGRESS_FILE = PROJECT_ROOT / "evaluation" / "ragas_progress.csv"
DELAY_BETWEEN_QUESTIONS = 120  # detik antar soal


def run_ragas_evaluation(collected_results, batch_size=5):
    """
    Run RAGAS evaluation satu per satu dengan Gemini + delay besar.
    Progress disimpan ke CSV agar bisa resume kalau terhenti.
    """
    from ragas import evaluate, RunConfig
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset
    import pandas as pd

    print("\n🔧 Mengkonfigurasi LLM Gemini untuk RAGAS...")
    llm_judge, emb_judge = _setup_ragas_llm()
    if not llm_judge:
        return None

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    # Load progress agar tidak mengulang yang sudah sukses
    if PROGRESS_FILE.exists():
        evaluated_df = pd.read_csv(PROGRESS_FILE)
        evaluated_ids = set(evaluated_df['id'].tolist())
        print(f"   ⏩ Melanjutkan... ({len(evaluated_ids)}/{len(collected_results)} soal sudah dinilai)")
    else:
        evaluated_df = pd.DataFrame()
        evaluated_ids = set()

    # Timeout 10 menit per soal, single-threaded
    run_config = RunConfig(max_workers=1, timeout=600)

    remaining = [r for r in collected_results if r["id"] not in evaluated_ids]
    total = len(collected_results)

    if not remaining:
        print(f"\n✅ Semua {total} soal sudah dinilai!")
    else:
        print(f"\n🔬 Evaluasi RAGAS: {len(remaining)} soal tersisa (delay {DELAY_BETWEEN_QUESTIONS}s antar soal)...")

    for idx, item in enumerate(remaining):
        qnum = item["id"]
        print(f"\n   📊 [{qnum}/{total}] {item['question'][:55]}...")

        ds = Dataset.from_dict({
            "question": [item["question"]],
            "answer": [item["answer"]],
            "contexts": [item["contexts"]],
            "ground_truth": [item["ground_truth"]],
        })

        success = False
        for attempt in range(5):
            try:
                result = evaluate(
                    ds,
                    metrics=metrics,
                    llm=llm_judge,
                    embeddings=emb_judge,
                    run_config=run_config
                )

                res_df = result.to_pandas()
                res_df['id'] = qnum

                # Print skor per pertanyaan
                for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                    if m in res_df.columns:
                        print(f"      {m}: {res_df[m].iloc[0]:.4f}")

                evaluated_df = pd.concat([evaluated_df, res_df], ignore_index=True)
                evaluated_df.to_csv(PROGRESS_FILE, index=False)

                success = True
                break

            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    wait_time = DELAY_BETWEEN_QUESTIONS * (attempt + 1)
                    print(f"      ⚠️ Rate limit! Menunggu {wait_time}s (attempt {attempt+1}/5)...")
                    time.sleep(wait_time)
                else:
                    print(f"      ❌ Error: {err[:150]}")
                    break

        if success:
            print(f"      ✅ Selesai!")
            # Delay antar soal (kecuali soal terakhir)
            if idx < len(remaining) - 1:
                print(f"      ⏳ Menunggu {DELAY_BETWEEN_QUESTIONS}s sebelum soal berikutnya...")
                time.sleep(DELAY_BETWEEN_QUESTIONS)

    # --- Build final result object dari CSV ---
    if PROGRESS_FILE.exists():
        final_df = pd.read_csv(PROGRESS_FILE)
        evaluated_count = len(final_df)
        print(f"\n📊 Total soal yang berhasil dinilai: {evaluated_count}/{total}")

        if evaluated_count == 0:
            return None

        overall = {}
        for m in ["context_precision", "context_recall", "faithfulness", "answer_relevancy"]:
            if m in final_df.columns:
                overall[m] = float(final_df[m].mean())
            else:
                overall[m] = 0.0

        class BatchedRagasResult:
            def __init__(self, scores_dict, dataframe):
                self._scores = scores_dict
                self._df = dataframe
            def __getitem__(self, key):
                return self._scores[key]
            def to_pandas(self):
                return self._df

        return BatchedRagasResult(overall, final_df)

    return None

def compute_per_category(collected_results, ragas_result):
    """
    Compute per-category breakdown for Tabel 16.
    Returns dict with category -> {context_precision, context_recall, avg_score}
    """
    # Get per-question scores from RAGAS result
    result_df = ragas_result.to_pandas()
    
    # Map scores back to categories
    category_scores = defaultdict(lambda: {
        "context_precision": [],
        "context_recall": [],
        "avg_score": [],
        "faithfulness": [],
        "answer_relevancy": [],
    })

    for i, item in enumerate(collected_results):
        cat = item["category"]
        row = result_df.iloc[i]
        category_scores[cat]["context_precision"].append(row.get("context_precision", 0))
        category_scores[cat]["context_recall"].append(row.get("context_recall", 0))
        category_scores[cat]["avg_score"].append(item["avg_score"])
        category_scores[cat]["faithfulness"].append(row.get("faithfulness", 0))
        category_scores[cat]["answer_relevancy"].append(row.get("answer_relevancy", 0))

    # Compute averages
    per_category = {}
    for cat, scores_dict in category_scores.items():
        per_category[cat] = {
            "display_name": CATEGORY_NAMES.get(cat, cat),
            "count": len(scores_dict["context_precision"]),
            "context_precision": round(
                sum(scores_dict["context_precision"]) / len(scores_dict["context_precision"]), 2
            ),
            "context_recall": round(
                sum(scores_dict["context_recall"]) / len(scores_dict["context_recall"]), 2
            ),
            "avg_score": round(
                sum(scores_dict["avg_score"]) / len(scores_dict["avg_score"]), 2
            ),
            "faithfulness": round(
                sum(scores_dict["faithfulness"]) / len(scores_dict["faithfulness"]), 2
            ),
            "answer_relevancy": round(
                sum(scores_dict["answer_relevancy"]) / len(scores_dict["answer_relevancy"]), 2
            ),
        }

    return per_category


def compute_latency_stats(collected_results):
    """
    Compute latency statistics for Tabel 19.
    Returns breakdown of retrieval, generation, and total latency.
    """
    retrieval = [r["retrieval_latency"] for r in collected_results]
    generation = [r["generation_latency"] for r in collected_results]
    total = [r["total_latency"] for r in collected_results]

    def stats(values):
        return {
            "avg": round(sum(values) / len(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }

    return {
        "retrieval": stats(retrieval),
        "generation": stats(generation),
        "total": stats(total),
    }


def build_per_question_table(collected_results, ragas_result):
    """
    Build per-question results for Tabel 18.
    Selects representative questions from each category.
    """
    result_df = ragas_result.to_pandas()
    per_question = []

    for i, item in enumerate(collected_results):
        row = result_df.iloc[i]
        # Summarize answer to max 80 chars
        answer = item["answer"]
        if len(answer) > 80:
            answer = answer[:77] + "..."

        per_question.append({
            "id": item["id"],
            "question": item["question"],
            "answer_summary": answer,
            "category": CATEGORY_NAMES.get(item["category"], item["category"]),
            "faithfulness": round(row.get("faithfulness", 0), 2),
            "answer_relevancy": round(row.get("answer_relevancy", 0), 2),
            "context_precision": round(row.get("context_precision", 0), 2),
            "context_recall": round(row.get("context_recall", 0), 2),
        })

    return per_question


# ============================================================
# Main Evaluation Flow
# ============================================================
def run_evaluation():
    """Run full RAGAS evaluation pipeline"""
    print("=" * 70)
    print("  EVALUASI RAGAS - SINEMA RAG CHATBOT")
    print(f"  Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Metode: BAB II - RAGAS Framework")
    print("=" * 70)

    # 1. Load benchmark dataset
    print("\n📂 Memuat benchmark dataset...")
    questions = load_benchmark_dataset()
    print(f"   Total pertanyaan: {len(questions)}")

    # Show category breakdown
    cats = defaultdict(int)
    for q in questions:
        cats[q["category"]] += 1
    for cat, count in cats.items():
        print(f"   - {CATEGORY_NAMES.get(cat, cat)}: {count} pertanyaan")

    # 2. Initialize RAG components
    print("\n🔄 Memuat komponen RAG...")
    print(f"   Embedding: {EMBEDDING_MODEL}")
    print(f"   Chunk Size: {CHUNK_SIZE} | Overlap: {CHUNK_OVERLAP} | Top-K: {TOP_K}")

    retriever = RAGRetriever(
        documents_dir=DOCUMENTS_DIR,
        vector_db_dir=VECTOR_DB_DIR,
        embedding_model_name=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        top_k=TOP_K
    )
    retriever.initialize()
    generator = APIGenerator()

    # 3. Collect RAG responses (with resume support)
    cached_results = _load_cache()
    if cached_results:
        valid = sum(1 for r in cached_results if not _is_error_answer(r.get("answer", "")))
        error = sum(1 for r in cached_results if _is_error_answer(r.get("answer", "")))
        print(f"\n💾 Cache ditemukan: {len(cached_results)} responses ")
        print(f"   ✅ Valid: {valid} | ❌ Error: {error} | Perlu collect: {error}")
        if error == 0:
            print(f"   Semua pertanyaan sudah terjawab! Skip ke evaluasi RAGAS...")
    else:
        print(f"\n💾 Tidak ada cache, mengumpulkan semua {len(questions)} pertanyaan...")

    print(f"\n📝 Mengumpulkan respons RAG...\n")
    collected_results = collect_rag_responses(
        retriever, generator, questions, cached_results
    )

    # Check if we have enough valid responses
    valid_count = sum(1 for r in collected_results if not _is_error_answer(r["answer"]))
    error_count = len(collected_results) - valid_count
    if error_count > 0:
        print(f"\n⚠️ Masih ada {error_count} pertanyaan dengan jawaban error.")
        print(f"   Jalankan ulang script ini nanti setelah API limit reset.")
        print(f"   Progress tersimpan di cache, tidak perlu ulang dari awal.")


    # 4. Run RAGAS evaluation
    ragas_result = run_ragas_evaluation(collected_results)

    if ragas_result is None:
        print("\n❌ Evaluasi RAGAS gagal. Menyimpan hasil parsial...")
        # Save partial results (latency only)
        partial_output = {
            "timestamp": datetime.now().isoformat(),
            "status": "partial - RAGAS evaluation failed",
            "config": {
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "top_k": TOP_K,
                "embedding_model": EMBEDDING_MODEL,
                "total_questions": len(questions),
            },
            "latency": compute_latency_stats(collected_results),
            "raw_responses": [
                {
                    "id": r["id"],
                    "question": r["question"],
                    "answer": r["answer"][:300],
                    "category": r["category"],
                    "avg_score": r["avg_score"],
                    "total_latency": r["total_latency"],
                }
                for r in collected_results
            ],
        }
        OUTPUT_FILE.parent.mkdir(exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(partial_output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Hasil parsial disimpan ke: {OUTPUT_FILE}")
        return partial_output

    # 5. Compute aggregated metrics
    print("\n📊 Menghitung metrik aggregated...")

    # Overall RAGAS scores
    summary = {
        "context_precision": round(ragas_result["context_precision"], 4),
        "context_recall": round(ragas_result["context_recall"], 4),
        "faithfulness": round(ragas_result["faithfulness"], 4),
        "answer_relevancy": round(ragas_result["answer_relevancy"], 4),
    }

    # Per-category (Tabel 16)
    per_category = compute_per_category(collected_results, ragas_result)

    # Per-question (Tabel 18)
    per_question = build_per_question_table(collected_results, ragas_result)

    # Latency (Tabel 19)
    latency = compute_latency_stats(collected_results)

    # 6. Print summary
    print("\n" + "=" * 70)
    print("  📈 HASIL EVALUASI RAGAS")
    print("=" * 70)

    # Tabel 15: Overall retrieval
    print("\n  📋 Tabel 15 - Evaluasi Retrieval:")
    for metric in ["context_precision", "context_recall"]:
        val = summary[metric]
        target = TARGETS[metric]
        status = "✅" if val >= target else "❌"
        print(f"     {metric:25s}: {val:.4f}  (target ≥ {target})  {status}")

    # Tabel 16: Per-category
    print("\n  📋 Tabel 16 - Per Kategori:")
    print(f"     {'Kategori':<25s} {'C.Prec':>8s} {'C.Recall':>10s} {'Avg Score':>10s}")
    print(f"     {'-'*25} {'-'*8} {'-'*10} {'-'*10}")
    for cat, data in per_category.items():
        print(f"     {data['display_name']:<25s} {data['context_precision']:>8.2f} {data['context_recall']:>10.2f} {data['avg_score']:>10.2f}")

    # Tabel 17: Overall generation
    print("\n  📋 Tabel 17 - Evaluasi Generation:")
    for metric in ["faithfulness", "answer_relevancy"]:
        val = summary[metric]
        target = TARGETS[metric]
        status = "✅" if val >= target else "❌"
        print(f"     {metric:25s}: {val:.4f}  (target ≥ {target})  {status}")

    # Tabel 19: Latency
    print("\n  📋 Tabel 19 - Latency:")
    print(f"     {'Komponen':<25s} {'Avg':>8s} {'Min':>8s} {'Max':>8s}")
    print(f"     {'-'*25} {'-'*8} {'-'*8} {'-'*8}")
    for comp in ["retrieval", "generation", "total"]:
        d = latency[comp]
        print(f"     {comp:<25s} {d['avg']:>7.2f}s {d['min']:>7.2f}s {d['max']:>7.2f}s")

    # 7. Save full results
    evaluation_output = {
        "timestamp": datetime.now().isoformat(),
        "status": "complete",
        "config": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "top_k": TOP_K,
            "embedding_model": EMBEDDING_MODEL,
            "total_questions": len(questions),
        },
        "targets": TARGETS,
        "summary": summary,
        "target_status": {
            metric: {
                "value": summary[metric],
                "target": TARGETS[metric],
                "achieved": summary[metric] >= TARGETS[metric],
            }
            for metric in TARGETS
        },
        "per_category": per_category,
        "per_question": per_question,
        "latency": latency,
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(evaluation_output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Hasil lengkap disimpan ke: {OUTPUT_FILE}")
    print("=" * 70)

    return evaluation_output


if __name__ == "__main__":
    run_evaluation()
