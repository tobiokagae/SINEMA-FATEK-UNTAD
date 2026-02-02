# -*- coding: utf-8 -*-
"""Script to rebuild vector index after adding category metadata"""

import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.retriever import RAGRetriever
from app.config import DOCUMENTS_DIR, VECTOR_DB_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, RELEVANCE_THRESHOLD

def main():
    print("=" * 60)
    print("REBUILDING VECTOR INDEX (with Category Metadata)")
    print("=" * 60)

    print(f"\nDocuments dir: {DOCUMENTS_DIR}")
    print(f"Vector DB dir: {VECTOR_DB_DIR}")
    print(f"Config: CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}")

    # Initialize retriever with force_reload
    print("\n[*] Initializing retriever with force_reload=True...")
    retriever = RAGRetriever(
        documents_dir=DOCUMENTS_DIR,
        vector_db_dir=VECTOR_DB_DIR,
        embedding_model_name=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        top_k=TOP_K,
        use_reranker=True,
        relevance_threshold=RELEVANCE_THRESHOLD
    )

    # Rebuild index
    retriever.initialize(force_reload=True)

    print("\n[OK] Index rebuilt successfully!")
    print("\n" + "=" * 60)

    # Verify category metadata
    print("\n[*] Verifying category metadata...")
    results = retriever.retrieve("poin ekstrakurikuler", top_k=5)

    if results:
        print(f"\n[OK] Sample chunks with category metadata:")
        for i, (doc, score) in enumerate(results[:3], 1):
            category = doc.metadata.get('category', 'unknown')
            source = doc.metadata.get('source', 'unknown')
            print(f"  {i}. [{category}] {source} (score: {score:.4f})")

    # Test query expansion
    print("\n[*] Testing query expansion...")
    test_queries = [
        "mengumpulkan poin",
        "syarat sidang skripsi",
        "klaim poin ekstrakurikuler"
    ]

    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = retriever.retrieve(query, top_k=3)

        if results:
            top_category = results[0][0].metadata.get('category', 'unknown')
            top_source = results[0][0].metadata.get('source', 'unknown')
            print(f"  [OK] Top result: [{top_category}] {top_source} (score: {results[0][1]:.4f})")
        else:
            print(f"  [X] No results found")

    print("\n" + "=" * 60)
    print("REBUILD COMPLETE! Ready to test with /chat endpoint")
    print("=" * 60)

if __name__ == "__main__":
    main()
