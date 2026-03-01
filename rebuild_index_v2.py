import sys
sys.path.insert(0, r'c:\Users\USER\Documents\kuliah\Skripsi Aclisung\PROJECT\sinema-chatbot')

from pathlib import Path
from app.config import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, RELEVANCE_THRESHOLD
from app.rag.retriever import RAGRetriever

retriever = RAGRetriever(
    documents_dir=Path("documents"),
    vector_db_dir=Path("vector_db"),
    embedding_model_name=EMBEDDING_MODEL,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    top_k=TOP_K,
    relevance_threshold=RELEVANCE_THRESHOLD
)

retriever.initialize(force_reload=True)  # force rebuild dari awal
print("Done! Index sudah di-rebuild.")
