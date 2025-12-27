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
    
    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """Retrieve relevant documents for a query"""
        if not self._initialized:
            self.initialize()
        
        k = top_k or self.top_k
        results = self.vector_store.search(query, top_k=k)
        
        return results
    
    def get_context(self, query: str, top_k: int = None) -> str:
        """Get formatted context string from retrieved documents"""
        results = self.retrieve(query, top_k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get('source', 'unknown')
            context_parts.append(f"[Sumber {i}: {source}]\n{doc.content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def refresh_index(self):
        """Reload all documents and rebuild index"""
        self.initialize(force_reload=True)
