"""Debug script to test RAG retrieval"""
import os
import sys
sys.path.insert(0, os.getcwd())

from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore

def main():
    print("=" * 60)
    print("DEBUGGING RAG RETRIEVAL")
    print("=" * 60)
    
    # Load embedding model
    print("\n1. Loading embedding model...")
    embedding = EmbeddingModel()
    
    # Load vector store
    print("\n2. Loading vector store...")
    vector_store = VectorStore(embedding_model=embedding, persist_dir="vector_db")
    vector_store.load()
    
    # Test query
    test_queries = [
        "IPK 2.35 bisa sidang skripsi?",
        "IPK minimal untuk sidang skripsi",
        "syarat sidang skripsi",
        "cara bayar UKT",
        "prosedur skripsi"
    ]
    
    print("\n3. Testing retrieval...")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.search(query, top_k=5)
        
        if results:
            for doc, score in results:
                source = doc.metadata.get('source', 'unknown')
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  [{score:.3f}] {source}: {content_preview}...")
        else:
            print("  No results found!")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
