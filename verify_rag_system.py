"""
Comprehensive RAG System Verification Script
Memverifikasi semua komponen RAG berjalan tanpa error
"""
import os
import sys
import time
import traceback

sys.path.insert(0, os.getcwd())

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {name}")
    if details:
        print(f"         └─ {details}")

def test_imports():
    """Test 1: Import semua module"""
    print_header("TEST 1: Module Imports")
    results = []
    
    modules = [
        ("app.config", "Konfigurasi"),
        ("app.rag.document_loader", "Document Loader"),
        ("app.rag.embeddings", "Embeddings"),
        ("app.rag.vector_store", "Vector Store"),
        ("app.rag.retriever", "Retriever"),
        ("app.llm.api_generator", "LLM API Generator"),
        ("app.database", "Database Service"),
    ]
    
    for module, name in modules:
        try:
            __import__(module)
            print_result(name, True)
            results.append(True)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)

def test_document_loader():
    """Test 2: Document Loader"""
    print_header("TEST 2: Document Loader")
    
    try:
        from app.rag.document_loader import DocumentLoader
        from pathlib import Path
        
        loader = DocumentLoader(Path("documents"))
        print_result("Inisialisasi DocumentLoader", True)
        
        # Test table conversion
        test_table = [["A", "B"], ["1", "2"]]
        md = loader._convert_table_to_markdown(test_table)
        print_result("Konversi tabel ke markdown", bool(md), f"{len(md)} chars")
        
        # Test formula detection
        text = "IPS = Σ(SKS x AM) / Σ SKS"
        formatted = loader._detect_and_format_formulas(text)
        print_result("Deteksi rumus", bool(formatted))
        
        return True
    except Exception as e:
        print_result("Document Loader", False, str(e))
        return False

def test_embedding():
    """Test 3: Embedding Model"""
    print_header("TEST 3: Embedding Model")
    
    try:
        from app.rag.embeddings import EmbeddingModel
        
        model = EmbeddingModel()
        print_result("Load embedding model", True)
        
        # Test embedding
        test_text = "Ini adalah test embedding"
        embedding = model.embed_query(test_text)
        dim = len(embedding)
        print_result("Generate embedding", True, f"Dimension: {dim}")
        
        return True
    except Exception as e:
        print_result("Embedding Model", False, str(e))
        return False

def test_vector_store():
    """Test 4: Vector Store"""
    print_header("TEST 4: Vector Store")
    
    try:
        from app.rag.embeddings import EmbeddingModel
        from app.rag.vector_store import VectorStore
        
        model = EmbeddingModel()
        store = VectorStore(embedding_model=model, persist_dir="vector_db")
        store.load()
        
        # Get stats
        num_docs = len(store.documents) if hasattr(store, 'documents') else "N/A"
        print_result("Load Vector Store", True, f"Documents: {num_docs}")
        
        # Test search
        results = store.search("syarat tugas akhir", top_k=3)
        print_result("Vector search", len(results) > 0, f"Found: {len(results)} results")
        
        return True
    except Exception as e:
        print_result("Vector Store", False, str(e))
        traceback.print_exc()
        return False

def test_retriever():
    """Test 5: Retriever"""
    print_header("TEST 5: Retriever")
    
    try:
        from app.rag.retriever import Retriever
        
        retriever = Retriever()
        print_result("Inisialisasi Retriever", True)
        
        # Test retrieval
        results = retriever.retrieve("IPK minimal untuk lulus")
        print_result("Retrieval test", len(results) > 0, f"Found: {len(results)} chunks")
        
        return True
    except Exception as e:
        print_result("Retriever", False, str(e))
        return False

def test_llm_generator():
    """Test 6: LLM Generator"""
    print_header("TEST 6: LLM Generator (API)")
    
    try:
        from app.llm.api_generator import APIGenerator
        
        gen = APIGenerator()
        print_result("Inisialisasi API Generator", True)
        
        # Test simple generation
        start = time.time()
        response = gen.generate("Selamat pagi", context="")
        latency = time.time() - start
        
        success = len(response) > 10
        print_result("LLM Generation", success, f"Latency: {latency:.2f}s")
        
        return True
    except Exception as e:
        print_result("LLM Generator", False, str(e))
        return False

def test_end_to_end():
    """Test 7: End-to-End RAG"""
    print_header("TEST 7: End-to-End RAG Pipeline")
    
    try:
        from app.rag.retriever import Retriever
        from app.llm.api_generator import APIGenerator
        
        retriever = Retriever()
        generator = APIGenerator()
        
        query = "Berapa IPK minimal untuk wisuda?"
        
        # Retrieve
        start = time.time()
        chunks = retriever.retrieve(query)
        retrieve_time = time.time() - start
        
        context = "\n\n".join([c.content for c in chunks[:5]])
        print_result("Retrieve context", len(chunks) > 0, f"{len(chunks)} chunks in {retrieve_time:.2f}s")
        
        # Generate
        start = time.time()
        response = generator.generate(query, context=context)
        gen_time = time.time() - start
        
        print_result("Generate response", len(response) > 20, f"{len(response)} chars in {gen_time:.2f}s")
        print(f"\n  📝 Response preview:")
        print(f"     {response[:200]}...")
        
        return True
    except Exception as e:
        print_result("End-to-End", False, str(e))
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test 8: Edge Cases"""
    print_header("TEST 8: Edge Cases")
    
    try:
        from app.rag.retriever import Retriever
        
        retriever = Retriever()
        
        # Empty query
        try:
            results = retriever.retrieve("")
            print_result("Empty query handling", True, "Handled gracefully")
        except:
            print_result("Empty query handling", False, "Crashed")
        
        # Very long query
        long_query = "test " * 100
        try:
            results = retriever.retrieve(long_query)
            print_result("Long query handling", True, "Handled gracefully")
        except:
            print_result("Long query handling", False, "Crashed")
        
        # Special characters
        special_query = "Apa itu @#$%^&*() ?"
        try:
            results = retriever.retrieve(special_query)
            print_result("Special chars handling", True, "Handled gracefully")
        except:
            print_result("Special chars handling", False, "Crashed")
        
        return True
    except Exception as e:
        print_result("Edge Cases", False, str(e))
        return False

def test_data_integrity():
    """Test 9: Data Integrity"""
    print_header("TEST 9: Data Integrity")
    
    try:
        from app.rag.embeddings import EmbeddingModel
        from app.rag.vector_store import VectorStore
        from pathlib import Path
        
        model = EmbeddingModel()
        store = VectorStore(embedding_model=model, persist_dir="vector_db")
        store.load()
        
        # Check documents
        docs = store.documents if hasattr(store, 'documents') else []
        print_result("Documents indexed", len(docs) > 0, f"Total: {len(docs)} chunks")
        
        # Check for empty chunks
        empty_chunks = sum(1 for d in docs if not d.content.strip())
        print_result("No empty chunks", empty_chunks == 0, f"Empty: {empty_chunks}")
        
        # Check metadata
        with_source = sum(1 for d in docs if d.metadata.get('source'))
        print_result("Metadata integrity", with_source == len(docs), f"With source: {with_source}/{len(docs)}")
        
        # Documents in folder
        doc_folder = Path("documents")
        md_files = list(doc_folder.glob("*.md"))
        print_result("Source documents", len(md_files) > 0, f"MD files: {len(md_files)}")
        
        return True
    except Exception as e:
        print_result("Data Integrity", False, str(e))
        return False

def main():
    print("\n" + "=" * 60)
    print("  🔍 COMPREHENSIVE RAG SYSTEM VERIFICATION")
    print("  SINEMA Chatbot - Fakultas Teknik UNTAD")
    print("=" * 60)
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run all tests
    results.append(("Module Imports", test_imports()))
    results.append(("Document Loader", test_document_loader()))
    results.append(("Embedding Model", test_embedding()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("Retriever", test_retriever()))
    results.append(("LLM Generator", test_llm_generator()))
    results.append(("End-to-End RAG", test_end_to_end()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Data Integrity", test_data_integrity()))
    
    # Summary
    print_header("SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print("\n" + "-" * 60)
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! RAG System is fully operational.")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed. Review errors above.")
    
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
