# -*- coding: utf-8 -*-
"""Reranker module using cross-encoder for improved retrieval accuracy"""
from typing import List, Tuple
from sentence_transformers import CrossEncoder

from .document_loader import Document


class Reranker:
    """Cross-encoder based reranker for improving retrieval precision"""
    
    # Multilingual reranker model (supports Indonesian + 100+ languages)
    DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None
        
    def _load_model(self):
        """Lazy load the reranker model"""
        if self._model is None:
            print(f"Loading reranker model: {self.model_name}")
            self._model = CrossEncoder(self.model_name, max_length=512)
            print("Reranker model loaded successfully")
    
    @property
    def model(self):
        self._load_model()
        return self._model
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[Document, float]],
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        """
        Rerank retrieved documents using cross-encoder.

        Args:
            query: The search query
            results: List of (Document, score) tuples from initial retrieval
            top_k: Number of top results to return after reranking

        Returns:
            Reranked list of (Document, score) tuples
        """
        if not results:
            return results

        # Prepare query-document pairs for cross-encoder
        pairs = [(query, doc.content) for doc, _ in results]

        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs)
        except Exception as e:
            print(f"[RERANKER] Error during reranking: {e}. Returning original results.")
            return results[:top_k] if top_k else results
        
        # Combine documents with new scores
        reranked = list(zip([doc for doc, _ in results], scores))
        
        # Sort by score descending
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k if specified
        if top_k and top_k < len(reranked):
            reranked = reranked[:top_k]
        
        return reranked
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model is not None
