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


def _load_api_keys():
    """
    Load all available OpenRouter API keys.
    Supports OPENROUTER_API_KEYS (comma-separated) and fallback OPENROUTER_API_KEY.
    """
    keys = []
    keys_str = os.getenv("OPENROUTER_API_KEYS", "")
    if keys_str:
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if not keys:
        single_key = os.getenv("OPENROUTER_API_KEY", "")
        if single_key:
            keys = [single_key]
    return keys


class _RotatingKeyManager:
    """Thread-safe API key rotation manager."""
    def __init__(self, keys):
        self.keys = keys
        self.index = 0
        self.lock = threading.Lock()
        self.call_count = 0

    def get_key(self):
        with self.lock:
            key = self.keys[self.index]
            self.call_count += 1
            # Rotate to next key every N calls to spread load
            if self.call_count % 3 == 0:
                self.index = (self.index + 1) % len(self.keys)
            return key

    def force_rotate(self):
        with self.lock:
            self.index = (self.index + 1) % len(self.keys)
            return self.keys[self.index]

    def set_key_index(self, idx):
        with self.lock:
            self.index = idx % len(self.keys)


# Global key manager (initialized in _setup_ragas_llm)
_key_manager = None


def _setup_ragas_llm():
    """
    Configure LLM for RAGAS evaluation using OpenRouter API.
    Supports multiple API keys with automatic rotation to avoid rate limits.
    """
    global _key_manager
    keys = _load_api_keys()
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    base_url = "https://openrouter.ai/api/v1"

    if not keys:
        print("❌ Tidak ada API key ditemukan di .env!")
        return None

    print(f"   🔑 Ditemukan {len(keys)} API key(s)")
    _key_manager = _RotatingKeyManager(keys)

    # CRITICAL: Set env vars so RAGAS internal clients (embeddings, etc.) work
    os.environ["OPENAI_API_KEY"] = keys[0]
    os.environ["OPENAI_BASE_URL"] = base_url

    # Use LangchainLLMWrapper with ChatOpenAI (most reliable for key rotation)
    try:
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            api_key=keys[0],
            base_url=base_url,
        )
        wrapped = LangchainLLMWrapper(llm)
        print(f"   ✅ RAGAS LLM configured via LangchainLLMWrapper ({model})")
        return wrapped, llm  # Return both so we can swap keys on the ChatOpenAI
    except (ImportError, Exception) as e:
        print(f"   ⚠️ LangchainLLMWrapper gagal: {e}")

    # Fallback: Set OPENAI_API_KEY env var
    try:
        os.environ["OPENAI_API_KEY"] = keys[0]
        os.environ["OPENAI_BASE_URL"] = base_url
        print(f"   ✅ RAGAS configured via env var (fallback, 1 key only)")
        return None, None
    except Exception as e:
        print(f"   ❌ Semua metode konfigurasi gagal: {e}")
        return None, None


def run_ragas_evaluation(collected_results, batch_size=5, delay_between_batches=5):
    """
    Run RAGAS evaluation on collected results with batch processing
    and API key rotation to avoid rate limits.

    Computes: context_precision, context_recall, faithfulness, answer_relevancy

    Args:
        collected_results: list of dicts from collect_rag_responses
        batch_size: number of questions per batch (default 5)
        delay_between_batches: seconds to wait between batches (default 5)

    Returns dict with per-question scores and aggregated metrics.
    """
    global _key_manager

    try:
        from ragas import evaluate
        from ragas.metrics import (
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        )
        from datasets import Dataset
        import pandas as pd
    except ImportError as e:
        print(f"\n❌ Error: Library RAGAS belum terinstal!")
        print(f"   Jalankan: pip install ragas datasets")
        print(f"   Detail: {e}")
        return None

    print("\n🔧 Mengkonfigurasi LLM untuk RAGAS...")
    setup_result = _setup_ragas_llm()
    if setup_result is None:
        return None
    ragas_llm, raw_llm = setup_result

    metrics = [context_precision, context_recall, faithfulness, answer_relevancy]
    total = len(collected_results)
    num_batches = (total + batch_size - 1) // batch_size

    print(f"\n🔬 Menjalankan evaluasi RAGAS...")
    print(f"   Total pertanyaan: {total}")
    print(f"   Batch size: {batch_size} | Total batches: {num_batches}")
    print(f"   Delay antar batch: {delay_between_batches}s")
    if _key_manager:
        print(f"   API keys: {len(_key_manager.keys)} keys (auto-rotation)")
    print(f"   Metrik: context_precision, context_recall, faithfulness, answer_relevancy")

    all_batch_dfs = []
    failed_batches = []

    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch = collected_results[start:end]

        # Rotate API key for this batch
        if _key_manager:
            _key_manager.set_key_index(batch_idx)
            new_key = _key_manager.get_key()
            # Update env var so RAGAS internal clients also use the rotated key
            os.environ["OPENAI_API_KEY"] = new_key
            if raw_llm is not None:
                raw_llm.openai_api_key = new_key
            key_suffix = new_key[-6:]
        else:
            key_suffix = "default"

        print(f"\n   📦 Batch {batch_idx + 1}/{num_batches} "
              f"(Q{start + 1}-Q{end}) | Key: ...{key_suffix}")

        # Prepare data for this batch
        ragas_data = {
            "question": [r["question"] for r in batch],
            "answer": [r["answer"] for r in batch],
            "contexts": [r["contexts"] for r in batch],
            "ground_truth": [r["ground_truth"] for r in batch],
        }
        dataset = Dataset.from_dict(ragas_data)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if ragas_llm is not None:
                    result = evaluate(dataset, metrics=metrics, llm=ragas_llm)
                else:
                    result = evaluate(dataset, metrics=metrics)

                batch_df = result.to_pandas()
                all_batch_dfs.append(batch_df)
                print(f"      ✅ Batch {batch_idx + 1} selesai!")

                # Print batch summary
                for m in ["context_precision", "context_recall",
                          "faithfulness", "answer_relevancy"]:
                    if m in batch_df.columns:
                        avg = batch_df[m].mean()
                        print(f"         {m}: {avg:.4f}")
                break

            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "429" in error_msg or "rate limit" in error_msg.lower()

                if is_rate_limit and attempt < max_retries - 1:
                    # Rotate to next key and wait longer
                    if _key_manager:
                        new_key = _key_manager.force_rotate()
                        os.environ["OPENAI_API_KEY"] = new_key
                        if raw_llm is not None:
                            raw_llm.openai_api_key = new_key
                        key_suffix = new_key[-6:]
                    wait = delay_between_batches * (attempt + 2)
                    print(f"      ⚠️ Rate limit hit! Rotating key → ...{key_suffix}")
                    print(f"         Menunggu {wait}s sebelum retry "
                          f"(attempt {attempt + 2}/{max_retries})...")
                    time.sleep(wait)
                else:
                    print(f"      ❌ Batch {batch_idx + 1} gagal: {error_msg[:120]}")
                    failed_batches.append(batch_idx + 1)
                    break

        # Delay between batches to respect rate limits
        if batch_idx < num_batches - 1:
            print(f"      ⏳ Menunggu {delay_between_batches}s...", end="", flush=True)
            time.sleep(delay_between_batches)
            print(" lanjut!")

    if not all_batch_dfs:
        print("\n❌ Semua batch gagal!")
        return None

    if failed_batches:
        print(f"\n⚠️ Batch yang gagal: {failed_batches}")
        print(f"   Evaluasi dilanjutkan dengan {len(all_batch_dfs)}/{num_batches} batch")

    # Merge all batch results into a single DataFrame
    merged_df = pd.concat(all_batch_dfs, ignore_index=True)

    # Compute overall averages
    overall = {}
    for m in ["context_precision", "context_recall",
              "faithfulness", "answer_relevancy"]:
        if m in merged_df.columns:
            overall[m] = float(merged_df[m].mean())
        else:
            overall[m] = 0.0

    # Create a result-like object that has both dict access and to_pandas()
    class BatchedRagasResult:
        def __init__(self, scores_dict, dataframe):
            self._scores = scores_dict
            self._df = dataframe

        def __getitem__(self, key):
            return self._scores[key]

        def to_pandas(self):
            return self._df

    return BatchedRagasResult(overall, merged_df)


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
