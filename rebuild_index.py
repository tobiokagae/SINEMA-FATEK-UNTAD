"""Script to rebuild the vector index"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, DOCUMENTS_DIR

def main():
    print("=" * 50)
    print("REBUILDING VECTOR INDEX")
    print("=" * 50)
    print(f"Config: CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}")
    
    # Category mapping based on filename patterns
    CATEGORY_MAP = {
        'panduan_ta': 'panduan_ta',
        'ta_non': 'panduan_ta',
        'tugas_akhir': 'panduan_ta',
        'integritas': 'integritas_akademik',
        'akademik_fatek': 'panduan_akademik',
        'panduan_akademik': 'panduan_akademik',
        'sinema': 'panduan_sinema',
        'ekstrakurikuler': 'panduan_sinema',
        'poin_ekskul': 'panduan_sinema',
        'satuan_poin': 'panduan_sinema'
    }
    
    def get_category(filename):
        """Determine category from filename"""
        filename_lower = filename.lower()
        for key, category in CATEGORY_MAP.items():
            if key in filename_lower:
                return category
        return 'uncategorized'
    
    # Load documents with config from app/config.py
    print("\n1. Loading documents...")
    loader = DocumentLoader(DOCUMENTS_DIR, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    # Load each document with category (only .md files to avoid duplicates with PDFs)
    all_documents = []
    documents_dir = loader.documents_dir
    for file_path in documents_dir.iterdir():
        # Only load .md files (PDFs have been converted to MD already)
        if file_path.suffix.lower() in {'.md', '.markdown'}:
            category = get_category(file_path.name)
            try:
                docs = loader.load_document(file_path, category=category)
                all_documents.extend(docs)
                print(f"   Loaded {len(docs)} chunks from {file_path.name} (category: {category})")
            except Exception as e:
                print(f"   Error loading {file_path.name}: {e}")
    
    print(f"\n   Total: {len(all_documents)} document chunks")
    
    # Create embeddings
    print("\n2. Creating embeddings...")
    embedding = EmbeddingModel()
    
    # Create new vector store
    print("\n3. Building FAISS index...")
    vector_store = VectorStore(embedding_model=embedding, persist_dir="vector_db")
    vector_store.add_documents(all_documents)
    
    # Save
    print("\n4. Saving index...")
    vector_store.save()
    
    print("\n" + "=" * 50)
    print("INDEX REBUILT SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    main()
