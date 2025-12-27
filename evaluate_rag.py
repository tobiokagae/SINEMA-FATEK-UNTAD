# -*- coding: utf-8 -*-
"""
Evaluasi RAG SINEMA Chatbot
Script untuk mengevaluasi performa retrieval dan response chatbot
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.retriever import RAGRetriever
from app.llm.api_generator import APIGenerator
from app.config import (
    DOCUMENTS_DIR, VECTOR_DB_DIR, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, SYSTEM_PROMPT
)

# Sample questions untuk evaluasi
EVALUATION_QUESTIONS = [
    {
        "question": "Apa syarat untuk mengikuti tugas akhir?",
        "expected_topics": ["tugas akhir", "syarat", "persyaratan"],
        "category": "Panduan TA"
    },
    {
        "question": "Berapa IPK minimal untuk lulus?",
        "expected_topics": ["IPK", "minimal", "kelulusan"],
        "category": "Panduan Akademik"
    },
    {
        "question": "Apa sanksi plagiarisme?",
        "expected_topics": ["plagiarisme", "sanksi", "integritas"],
        "category": "Integritas Akademik"
    },
    {
        "question": "Bagaimana cara mendapatkan poin ekstrakurikuler?",
        "expected_topics": ["poin", "ekstrakurikuler", "kegiatan"],
        "category": "SINEMA"
    },
    {
        "question": "Apakah bisa mengulang mata kuliah untuk perbaikan nilai?",
        "expected_topics": ["mengulang", "perbaikan", "nilai"],
        "category": "Panduan Akademik"
    },
    {
        "question": "Berapa lama masa studi maksimal?",
        "expected_topics": ["masa studi", "maksimal", "semester"],
        "category": "Panduan Akademik"
    },
    {
        "question": "Apa itu SINEMA?",
        "expected_topics": ["SINEMA", "sistem", "informasi"],
        "category": "SINEMA"
    },
    {
        "question": "Bagaimana prosedur pengajuan cuti akademik?",
        "expected_topics": ["cuti", "akademik", "prosedur"],
        "category": "Panduan Akademik"
    },
]


def evaluate_retrieval(retriever, question, expected_topics):
    """Evaluate retrieval quality for a single question"""
    results = retriever.retrieve(question)
    
    # Check if expected topics are found in retrieved documents
    found_topics = []
    top_scores = []
    
    for doc, score in results[:5]:  # Check top 5 results
        content = doc.page_content.lower()
        top_scores.append(score)
        for topic in expected_topics:
            if topic.lower() in content and topic not in found_topics:
                found_topics.append(topic)
    
    # Calculate metrics
    precision = len(found_topics) / len(expected_topics) if expected_topics else 0
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
    
    return {
        "found_topics": found_topics,
        "missing_topics": [t for t in expected_topics if t not in found_topics],
        "precision": precision,
        "avg_score": avg_score,
        "top_5_scores": [round(s, 4) for s in top_scores]
    }


def evaluate_generation(generator, retriever, question):
    """Evaluate response generation for a single question"""
    # Get context
    results = retriever.retrieve(question)
    context_parts = [doc.page_content for doc, _ in results[:TOP_K]]
    context = "\n\n".join(context_parts)
    
    # Generate response
    response, latency = generator.generate(
        query=question,
        context=context,
        system_prompt=SYSTEM_PROMPT,
        conversation_history=[]
    )
    
    # Check response quality
    is_fallback = "tidak menemukan" in response.lower() or "tidak ada informasi" in response.lower()
    word_count = len(response.split())
    
    return {
        "response": response[:500] + "..." if len(response) > 500 else response,
        "latency_seconds": round(latency, 2),
        "word_count": word_count,
        "is_fallback": is_fallback
    }


def run_evaluation():
    """Run full RAG evaluation"""
    print("=" * 60)
    print("EVALUASI RAG SINEMA CHATBOT")
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Configuration summary
    print("\n📊 KONFIGURASI:")
    print(f"   Chunk Size: {CHUNK_SIZE}")
    print(f"   Chunk Overlap: {CHUNK_OVERLAP}")
    print(f"   Top-K: {TOP_K}")
    print(f"   Embedding: {EMBEDDING_MODEL}")
    
    # Initialize components
    print("\n🔄 Memuat komponen...")
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
    
    # Run evaluation
    print(f"\n📝 Mengevaluasi {len(EVALUATION_QUESTIONS)} pertanyaan...\n")
    
    results = []
    total_precision = 0
    total_latency = 0
    fallback_count = 0
    
    for i, item in enumerate(EVALUATION_QUESTIONS, 1):
        question = item["question"]
        print(f"[{i}/{len(EVALUATION_QUESTIONS)}] {question}")
        
        # Evaluate retrieval
        retrieval_result = evaluate_retrieval(retriever, question, item["expected_topics"])
        
        # Evaluate generation
        generation_result = evaluate_generation(generator, retriever, question)
        
        # Combine results
        result = {
            "question": question,
            "category": item["category"],
            "retrieval": retrieval_result,
            "generation": generation_result
        }
        results.append(result)
        
        # Accumulate metrics
        total_precision += retrieval_result["precision"]
        total_latency += generation_result["latency_seconds"]
        if generation_result["is_fallback"]:
            fallback_count += 1
        
        # Print summary for this question
        status = "✅" if retrieval_result["precision"] >= 0.5 else "⚠️"
        print(f"   {status} Precision: {retrieval_result['precision']:.0%} | Latency: {generation_result['latency_seconds']}s")
    
    # Calculate overall metrics
    n = len(EVALUATION_QUESTIONS)
    avg_precision = total_precision / n
    avg_latency = total_latency / n
    success_rate = (n - fallback_count) / n
    
    # Print summary
    print("\n" + "=" * 60)
    print("📈 RINGKASAN EVALUASI")
    print("=" * 60)
    print(f"   Average Precision: {avg_precision:.1%}")
    print(f"   Average Latency: {avg_latency:.2f} seconds")
    print(f"   Success Rate: {success_rate:.1%} ({n - fallback_count}/{n} questions)")
    print(f"   Fallback Responses: {fallback_count}")
    
    # Save results to JSON
    output_file = Path(__file__).parent / "evaluation" / "evaluation_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    evaluation_output = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "top_k": TOP_K,
            "embedding_model": EMBEDDING_MODEL
        },
        "summary": {
            "avg_precision": round(avg_precision, 4),
            "avg_latency_seconds": round(avg_latency, 2),
            "success_rate": round(success_rate, 4),
            "total_questions": n,
            "fallback_count": fallback_count
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Hasil disimpan ke: {output_file}")
    print("=" * 60)
    
    return evaluation_output


if __name__ == "__main__":
    run_evaluation()
