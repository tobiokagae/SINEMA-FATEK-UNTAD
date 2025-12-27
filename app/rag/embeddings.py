# -*- coding: utf-8 -*-
"""Embedding generation using Sentence Transformers - GPU OPTIMIZED"""
from typing import List
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """Generate embeddings for text using Sentence Transformers with GPU support"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device: str = None):
        self.model_name = model_name
        # Auto-detect GPU if device not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model on specified device"""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            print(f"Using device: {self.device}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            print(f"Embedding model loaded successfully on {self.device.upper()}")
        return self._model
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()
