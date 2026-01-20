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
    
    def search_mmr(self, query: str, top_k: int = 5, fetch_k: int = 20, 
                   lambda_mult: float = 0.7, diversity_boost: float = 0.3) -> List[Tuple[Document, float]]:
        """
        Search using Maximal Marginal Relevance for diverse results.
        
        MMR balances relevance and diversity to ensure results from different 
        source documents are included.
        
        Args:
            query: Search query
            top_k: Number of results to return
            fetch_k: Number of candidates to fetch initially (should be > top_k)
            lambda_mult: Balance between relevance (1) and diversity (0). Default 0.7
            diversity_boost: Extra score boost for chunks from new source documents
        
        Returns:
            List of (Document, score) tuples with diverse results
        """
        if self.index is None or len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Fetch more candidates than needed
        active_index = self.gpu_index if self.use_gpu and self.gpu_index is not None else self.index
        k = min(fetch_k, len(self.documents))
        scores, indices = active_index.search(query_embedding, k)
        
        # Filter valid results
        candidates = []
        candidate_embeddings = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                candidates.append((self.documents[idx], float(score), idx))
        
        if not candidates:
            return []
        
        # Get embeddings for candidates (reconstruct from index)
        for _, _, idx in candidates:
            # Reconstruct embedding from FAISS index
            embedding = np.zeros((1, self.index.d), dtype=np.float32)
            self.index.reconstruct(int(idx), embedding[0])  # Convert to Python int
            candidate_embeddings.append(embedding[0])
        
        candidate_embeddings = np.array(candidate_embeddings)
        
        # MMR Selection
        selected = []
        selected_indices = set()
        selected_sources = set()  # Track unique source documents
        
        while len(selected) < min(top_k, len(candidates)):
            best_score = -float('inf')
            best_idx = -1
            
            for i, (doc, relevance_score, orig_idx) in enumerate(candidates):
                if i in selected_indices:
                    continue
                
                # Calculate MMR score
                if not selected:
                    # First selection: pure relevance
                    mmr_score = relevance_score
                else:
                    # Calculate max similarity to already selected
                    selected_embeddings = candidate_embeddings[list(selected_indices)]
                    similarities = np.dot(selected_embeddings, candidate_embeddings[i])
                    max_sim = np.max(similarities)
                    
                    # MMR: balance relevance and diversity
                    mmr_score = lambda_mult * relevance_score - (1 - lambda_mult) * max_sim
                
                # Boost score for new source documents (diversity across files)
                source = doc.metadata.get('source', 'unknown')
                if source not in selected_sources:
                    mmr_score += diversity_boost
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            if best_idx == -1:
                break
            
            doc, relevance_score, orig_idx = candidates[best_idx]
            selected.append((doc, relevance_score))
            selected_indices.add(best_idx)
            selected_sources.add(doc.metadata.get('source', 'unknown'))
        
        return selected
    
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

