"""Script to verify rebuilt index contains updated content"""
import os
import sys
sys.path.insert(0, os.getcwd())

from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore

def main():
    print("=" * 60)
    print("VERIFIKASI REBUILD INDEX")
    print("=" * 60)
    
    # Load components
    print("\nLoading embedding model dan vector store...")
    embedding = EmbeddingModel()
    vector_store = VectorStore(embedding_model=embedding, persist_dir="vector_db")
    vector_store.load()
    
    # Test queries untuk konten yang sudah diperbaiki
    test_queries = [
        "tabel nilai mutu angka mutu penilaian",
        "rumus IPS IPK semester",
        "rentang nilai akhir A B C D E"
    ]
    
    print("\n" + "-" * 60)
    print("HASIL PENCARIAN:")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\n>>> Query: '{query}'")
        results = vector_store.search(query, top_k=2)
        
        if results:
            for doc, score in results:
                source = doc.metadata.get('source', 'unknown')
                content = doc.page_content[:500].replace('\r', '').replace('\n', ' ')
                print(f"\n  [Score: {score:.3f}] {source}")
                print(f"  Content: {content}...")
        else:
            print("  Tidak ada hasil!")
    
    print("\n" + "=" * 60)
    print("VERIFIKASI SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    main()
