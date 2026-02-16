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


def collect_rag_responses(retriever, generator, questions):
    """
    Run RAG pipeline for each question and collect responses + contexts.
    Also measures latency per-component.

    Returns list of dicts with: question, answer, contexts, ground_truth,
    category, retrieval_latency, generation_latency, total_latency, avg_score
    """
    results = []
    total = len(questions)

    for i, item in enumerate(questions, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]
        category = item["category"]

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

        results.append({
            "id": item["id"],
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth,
            "category": category,
            "retrieval_latency": round(retrieval_latency, 4),
            "generation_latency": round(generation_latency, 4),
            "total_latency": round(total_latency, 4),
            "avg_score": round(avg_score, 4),
        })

        # Status indicator
        status = "✅" if avg_score > 0.3 else "⚠️"
        print(f"       {status} Score: {avg_score:.3f} | Latency: {total_latency:.2f}s")

    return results


def _setup_ragas_llm():
    """
    Configure LLM for RAGAS evaluation using OpenRouter API.
    Tries multiple approaches in order of preference.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    base_url = "https://openrouter.ai/api/v1"

    if not api_key:
        print("❌ OPENROUTER_API_KEY tidak ditemukan di .env!")
        return None

    # Approach 1: Use ragas.llms.llm_factory (recommended for ragas >= 0.2)
    try:
        from ragas.llms import llm_factory
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        llm = llm_factory(model, client=client)
        print(f"   ✅ RAGAS LLM configured via llm_factory ({model})")
        return llm
    except (ImportError, Exception) as e:
        print(f"   ⚠️ llm_factory gagal: {e}")

    # Approach 2: Use LangchainLLMWrapper with ChatOpenAI
    try:
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        wrapped = LangchainLLMWrapper(llm)
        print(f"   ✅ RAGAS LLM configured via LangchainLLMWrapper ({model})")
        return wrapped
    except (ImportError, Exception) as e:
        print(f"   ⚠️ LangchainLLMWrapper gagal: {e}")

    # Approach 3: Set OPENAI_API_KEY env var as fallback for RAGAS default behavior
    try:
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        print(f"   ✅ RAGAS configured via OPENAI_API_KEY env var (fallback)")
        return None  # Will use RAGAS default
    except Exception as e:
        print(f"   ❌ Semua metode konfigurasi gagal: {e}")
        return None


def run_ragas_evaluation(collected_results):
    """
    Run RAGAS evaluation on collected results.
    Computes: context_precision, context_recall, faithfulness, answer_relevancy

    Returns dict with per-question scores and aggregated metrics.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import (
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        )
        from datasets import Dataset
    except ImportError as e:
        print(f"\n❌ Error: Library RAGAS belum terinstal!")
        print(f"   Jalankan: pip install ragas datasets")
        print(f"   Detail: {e}")
        return None

    # Prepare data in RAGAS format
    ragas_data = {
        "question": [r["question"] for r in collected_results],
        "answer": [r["answer"] for r in collected_results],
        "contexts": [r["contexts"] for r in collected_results],
        "ground_truth": [r["ground_truth"] for r in collected_results],
    }

    dataset = Dataset.from_dict(ragas_data)

    print("\n🔧 Mengkonfigurasi LLM untuk RAGAS...")
    ragas_llm = _setup_ragas_llm()

    print("\n🔬 Menjalankan evaluasi RAGAS (ini bisa memakan waktu 5-15 menit)...")
    print("   Metrik: context_precision, context_recall, faithfulness, answer_relevancy")

    # Run RAGAS evaluation
    metrics = [context_precision, context_recall, faithfulness, answer_relevancy]

    try:
        if ragas_llm is not None:
            result = evaluate(dataset, metrics=metrics, llm=ragas_llm)
        else:
            result = evaluate(dataset, metrics=metrics)
    except Exception as e:
        print(f"\n❌ RAGAS evaluate gagal: {e}")
        return None

    return result


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

    # 3. Collect RAG responses
    print(f"\n📝 Mengumpulkan respons RAG untuk {len(questions)} pertanyaan...\n")
    collected_results = collect_rag_responses(retriever, generator, questions)

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
