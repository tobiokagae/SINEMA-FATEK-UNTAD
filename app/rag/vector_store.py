# -*- coding: utf-8 -*-
"""FAISS Vector Store for document storage and retrieval"""
import json
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss
import torch

from .document_loader import Document
from .embeddings import EmbeddingModel

class VectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self, embedding_model: EmbeddingModel, persist_dir: Path = None, use_gpu: bool = None):
        self.embedding_model = embedding_model
        self.persist_dir = Path(persist_dir) if persist_dir else None
        
        # Check if faiss-gpu is available (faiss-cpu doesn't have StandardGpuResources)
        has_gpu_faiss = hasattr(faiss, 'StandardGpuResources')
        
        # Auto-detect GPU if not specified
        if use_gpu is None:
            self.use_gpu = torch.cuda.is_available() and has_gpu_faiss
        else:
            self.use_gpu = use_gpu and torch.cuda.is_available() and has_gpu_faiss
        
        self.index: Optional[faiss.IndexFlatIP] = None
        self.gpu_index = None
        self.gpu_resource = None
        self.documents: List[Document] = []
        
        if self.use_gpu:
            print("FAISS Vector Store: GPU mode enabled")
            self.gpu_resource = faiss.StandardGpuResources()
        else:
            if not has_gpu_faiss:
                print("FAISS Vector Store: CPU mode (faiss-gpu not installed)")
            else:
                print("FAISS Vector Store: CPU mode")
    
    def _to_gpu_index(self, cpu_index):
        """Convert CPU index to GPU index"""
        if self.use_gpu and self.gpu_resource is not None:
            try:
                return faiss.index_cpu_to_gpu(self.gpu_resource, 0, cpu_index)
            except Exception as e:
                print(f"Failed to move index to GPU: {e}, using CPU")
                self.use_gpu = False
                return cpu_index
        return cpu_index
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        if not documents:
            print("No documents to add")
            return
        
        # Generate embeddings
        print(f"Generating embeddings for {len(documents)} documents...")
        texts = [doc.content for doc in documents]
        embeddings = self.embedding_model.embed_texts(texts)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create or update index
        if self.index is None:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity for normalized vectors
            if self.use_gpu:
                self.gpu_index = self._to_gpu_index(self.index)
        
        # Add to index (use GPU index if available)
        active_index = self.gpu_index if self.use_gpu and self.gpu_index is not None else self.index
        active_index.add(embeddings)
        
        # Keep CPU index in sync if using GPU
        if self.use_gpu and self.gpu_index is not None:
            self.index.add(embeddings)
        
        self.documents.extend(documents)
        
        device_info = "GPU" if self.use_gpu else "CPU"
        print(f"Added {len(documents)} documents on {device_info}. Total: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Search for similar documents"""
        if self.index is None or len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search (use GPU index if available)
        active_index = self.gpu_index if self.use_gpu and self.gpu_index is not None else self.index
        k = min(top_k, len(self.documents))
        scores, indices = active_index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save(self):
        """Save index and documents to disk"""
        if self.persist_dir is None:
            return
        
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index (always save CPU index for portability)
        if self.index is not None:
            index_path = self.persist_dir / "index.faiss"
            faiss.write_index(self.index, str(index_path))
        
        # Save documents metadata
        docs_data = [
            {"content": doc.content, "metadata": doc.metadata}
            for doc in self.documents
        ]
        docs_path = self.persist_dir / "documents.json"
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, ensure_ascii=False, indent=2)
        
        print(f"Vector store saved to {self.persist_dir}")
    
    def load(self) -> bool:
        """Load index and documents from disk"""
        if self.persist_dir is None:
            return False
        
        index_path = self.persist_dir / "index.faiss"
        docs_path = self.persist_dir / "documents.json"
        
        if not index_path.exists() or not docs_path.exists():
            return False
        
        # Load FAISS index (CPU first)
        self.index = faiss.read_index(str(index_path))
        
        # Transfer to GPU if available
        if self.use_gpu:
            self.gpu_index = self._to_gpu_index(self.index)
        
        # Load documents
        with open(docs_path, 'r', encoding='utf-8') as f:
            docs_data = json.load(f)
        
        self.documents = [
            Document(content=d["content"], metadata=d["metadata"])
            for d in docs_data
        ]
        
        device_info = "GPU" if self.use_gpu else "CPU"
        print(f"Loaded {len(self.documents)} documents from {self.persist_dir} on {device_info}")
        return True
    
    def clear(self):
        """Clear all documents and index"""
        self.index = None
        self.gpu_index = None
        self.documents = []

