"""
Edge Case Testing untuk SINEMA RAG Chatbot
Menguji batas kemampuan sistem dengan skenario tidak biasa
"""
import sys
import os
import time

sys.path.insert(0, os.getcwd())

from app.rag.retriever import RAGRetriever
from app.llm.api_generator import APIGenerator
from app.config import DOCUMENTS_DIR, VECTOR_DB_DIR, TOP_K

def test_edge_case(name, query, retriever, generator=None):
    """Run single edge case test"""
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
    print("-"*50)
    
    try:
        # Test retrieval
        start = time.time()
        results = retriever.retrieve(query)
        retrieve_time = time.time() - start
        
        print(f"[OK] Retrieval: {len(results)} results in {retrieve_time:.2f}s")
        
        if results:
            top_score = results[0][1]
            print(f"     Top score: {top_score:.3f}")
        
        # Test generation if generator provided
        if generator and results:
            context = "\n".join([r[0].content for r in results[:3]])
            start = time.time()
            response = generator.generate(query, context=context)
            gen_time = time.time() - start
            print(f"[OK] Generation: {len(response)} chars in {gen_time:.2f}s")
            print(f"     Preview: {response[:100]}...")
        
        return True, "PASS"
        
    except Exception as e:
        print(f"[FAIL] Error: {str(e)[:100]}")
        return False, str(e)

def main():
    print("\n" + "="*60)
    print("  EDGE CASE TESTING - SINEMA RAG CHATBOT")
    print("="*60)
    
    # Initialize
    print("\nInitializing RAG components...")
    retriever = RAGRetriever(DOCUMENTS_DIR, VECTOR_DB_DIR, top_k=TOP_K)
    retriever.initialize()
    generator = APIGenerator()
    print("Ready!\n")
    
    # Edge cases to test
    edge_cases = [
        # Empty/whitespace
        ("Query Kosong", ""),
        ("Query Spasi Saja", "   "),
        
        # Very long
        ("Query Sangat Panjang", "syarat " * 100),
        
        # Special characters
        ("Karakter Spesial", "@#$%^&*()!~`[]{}"),
        ("Mix Karakter", "Apa syarat @#$ untuk lulus???"),
        
        # Mixed language
        ("Bahasa Campuran", "What is the minimum IPK untuk lulus?"),
        ("Full English", "What are the graduation requirements?"),
        
        # Out of scope
        ("Di Luar Scope", "Siapa presiden Indonesia saat ini?"),
        ("Tidak Relevan", "Bagaimana cara memasak nasi goreng?"),
        
        # Typo/misspelling
        ("Typo Berat", "syrat tutgas ahkir"),
        ("Salah Ejaan", "berpa ipk miniml utk wisda?"),
        
        # Ambiguous
        ("Ambigu", "Berapa minimal?"),
        ("Terlalu Umum", "Jelaskan"),
        
        # Numbers only
        ("Angka Saja", "12345"),
        
        # Single word
        ("Satu Kata", "IPK"),
        
        # Very specific
        ("Sangat Spesifik", "Berapa poin ekstrakurikuler untuk kegiatan panitia seminar nasional sebagai ketua pelaksana?"),
    ]
    
    results = []
    
    for name, query in edge_cases:
        # Only use generator for some tests to save API calls
        use_gen = name in ["Bahasa Campuran", "Di Luar Scope", "Typo Berat", "Sangat Spesifik"]
        passed, msg = test_edge_case(name, query, retriever, generator if use_gen else None)
        results.append((name, passed, msg))
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    for name, passed, msg in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
    
    print("-"*60)
    print(f"  Total: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n  [SUCCESS] Semua edge case ditangani dengan baik!")
    else:
        failed = total - passed_count
        print(f"\n  [WARNING] {failed} test(s) gagal - perlu investigasi")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
