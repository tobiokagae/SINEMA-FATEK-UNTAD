# -*- coding: utf-8 -*-
"""RAG Retriever combining all components"""
from pathlib import Path
from typing import List, Tuple

from .document_loader import Document, DocumentLoader
from .embeddings import EmbeddingModel
from .vector_store import VectorStore

class RAGRetriever:
    """Retrieval-Augmented Generation retriever"""
    
    def __init__(
        self,
        documents_dir: Path,
        vector_db_dir: Path,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 3
    ):
        self.documents_dir = Path(documents_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.top_k = top_k
        
        # Initialize components
        self.document_loader = DocumentLoader(
            documents_dir=self.documents_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedding_model = EmbeddingModel(model_name=embedding_model_name)
        self.vector_store = VectorStore(
            embedding_model=self.embedding_model,
            persist_dir=self.vector_db_dir
        )
        
        self._initialized = False
    
    def initialize(self, force_reload: bool = False):
        """Initialize the retriever by loading or creating the index"""
        if self._initialized and not force_reload:
            return
        
        # Try to load existing index
        if not force_reload and self.vector_store.load():
            self._initialized = True
            return
        
        # Load and index documents
        print("Building new vector index...")
        documents = self.document_loader.load_all_documents()
        
        if documents:
            self.vector_store.clear()
            self.vector_store.add_documents(documents)
            self.vector_store.save()
        
        self._initialized = True
    
    def retrieve(self, query: str, top_k: int = None, use_mmr: bool = True) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_mmr: If True, use MMR for diverse results across documents
        
        Returns:
            List of (Document, score) tuples
        """
        if not self._initialized:
            self.initialize()
        
        k = top_k or self.top_k
        
        if use_mmr:
            # Use MMR for diverse results (fetch more candidates, return top_k)
            results = self.vector_store.search_mmr(
                query, 
                top_k=k, 
                fetch_k=k * 3,  # Fetch 3x candidates for better diversity
                lambda_mult=0.7,  # 70% relevance, 30% diversity
                diversity_boost=0.3  # Extra boost for new source documents
            )
        else:
            # Standard similarity search
            results = self.vector_store.search(query, top_k=k)
        
        return results
    
    def get_context(self, query: str, top_k: int = None) -> str:
        """Get formatted context string from retrieved documents with clear source labels"""
        results = self.retrieve(query, top_k)
        
        if not results:
            return ""
        
        # Map source filenames to readable names
        source_labels = {
            'PANDUAN_AKADEMIK_FATEK': '📘 Panduan Akademik FATEK (Jalur Skripsi)',
            'Buku_Panduan_TA_Non_Skripsi': '📗 Panduan TA Non-Skripsi',
            'PANDUAN_SATUAN_POIN_EKSTRAKURIKULER': '📙 Panduan Poin Ekstrakurikuler',
        }
        
        context_parts = []
        for i, (doc, score) in enumerate(results, 1):
            source_file = doc.metadata.get('source', 'unknown')
            
            # Get readable label or create one from filename
            readable_label = None
            for key, label in source_labels.items():
                if key in source_file:
                    readable_label = label
                    break
            
            if not readable_label:
                # Clean up filename for display
                readable_label = f"📄 {source_file.replace('_', ' ').replace('.md', '')}"
            
            context_parts.append(f"[SUMBER: {readable_label}]\n{doc.content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def refresh_index(self):
        """Reload all documents and rebuild index"""
        self.initialize(force_reload=True)
