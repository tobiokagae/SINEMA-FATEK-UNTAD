# -*- coding: utf-8 -*-
"""RAG Retriever combining all components"""
from pathlib import Path
from typing import List, Tuple

from .document_loader import Document, DocumentLoader
from .embeddings import EmbeddingModel
from .vector_store import VectorStore
from .reranker import Reranker

class RAGRetriever:
    """Retrieval-Augmented Generation retriever"""
    
    def __init__(
        self,
        documents_dir: Path,
        vector_db_dir: Path,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 3,
        use_reranker: bool = True,
        relevance_threshold: float = 0.3
    ):
        self.documents_dir = Path(documents_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.top_k = top_k
        self.use_reranker = use_reranker
        self.relevance_threshold = relevance_threshold
        
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
        
        # Initialize reranker if enabled
        self.reranker = Reranker() if use_reranker else None
        
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

        # Apply query expansion for better matching
        expanded_query = self._expand_query(query)

        # For reranking, fetch more candidates initially (increased for better coverage)
        fetch_k = k * 3 if self.use_reranker else k

        if use_mmr:
            # Use MMR for diverse results (fetch more candidates, return top_k)
            results = self.vector_store.search_mmr(
                expanded_query,  # Use expanded query
                top_k=fetch_k,
                fetch_k=fetch_k * 3,  # Fetch 3x candidates for better diversity
                lambda_mult=0.7,  # 70% relevance, 30% diversity
                diversity_boost=0.3  # Extra boost for new source documents
            )
        else:
            # Standard similarity search
            results = self.vector_store.search(expanded_query, top_k=fetch_k)

        # Apply category-based filtering before reranking
        if results:
            results = self._filter_by_category(query, results)
            print(f"[CATEGORY FILTER] After filtering: {len(results)} results")

        # Apply reranking if enabled - use ORIGINAL query for reranking
        if self.use_reranker and self.reranker and results:
            print(f"[RERANKER] Reranking {len(results)} results...")
            results = self.reranker.rerank(query, results, top_k=k)  # Use original query for reranking
            print(f"[RERANKER] Top result score: {results[0][1]:.4f}" if results else "")

        return results

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms for better retrieval

        Args:
            query: Original query

        Returns:
            Expanded query with synonyms
        """
        query_lower = query.lower()

        # Define expansion rules
        expansions = {
            # "mengumpulkan poin" → add "klaim", "pengajuan", "ekstrakurikuler"
            'mengumpulkan poin': ['mengumpulkan poin klaim ekstrakurikuler pengajuan'],
            'poin': ['poin ekstrakurikuler kegiatan spe'],
            # Add more expansions as needed
            'ekstrakurikuler': ['kegiatan kemahasiswaan organisasi lomba'],
            'klaim': ['pengajuan bukti sertifikat'],
        }

        # Check if query matches any expansion pattern
        for pattern, synonyms in expansions.items():
            if pattern in query_lower:
                # Add synonyms to query
                # Use both original and expanded for retrieval
                expanded = query + ' ' + ' '.join(synonyms)
                print(f"[QUERY EXPANSION] '{query}' -> '{expanded[:100]}...'")
                return expanded

        return query

    def _detect_query_category(self, query: str) -> str:
        """Detect the likely category of a query for better filtering

        Args:
            query: The search query

        Returns:
            Detected category
        """
        query_lower = query.lower()

        # Keyword-based category detection
        if any(word in query_lower for word in ['poin', 'ekstrakurikuler', 'spe', 'kegiatan', 'lomba', 'organisasi', 'ukm']):
            return 'poin_ekstrakurikuler'
        elif any(word in query_lower for word in ['skripsi', 'seminar proposal', 'seminar hasil', 'sidang skripsi']):
            return 'ta_skripsi'
        elif any(word in query_lower for word in ['non-skripsi', 'ta non', 'prototipe', 'karya']):
            return 'ta_non_skripsi'
        elif any(word in query_lower for word in ['sinema', 'dashboard', 'login', 'pengajuan']):
            return 'website_sinema'
        elif any(word in query_lower for word in ['plagiarisme', 'integritas', 'etalase']):
            return 'integritas'
        elif any(word in query_lower for word in ['transkrip', 'tem']):
            return 'transkrip_tem'
        elif any(word in query_lower for word in ['ipk', 'sks', 'nilai', 'krs', 'semester']):
            return 'panduan_akademik'

        return 'general'

    def _filter_by_category(self, query: str, results: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        """Filter results by category to improve relevance

        Args:
            query: The search query
            results: Retrieved documents with scores

        Returns:
            Filtered results
        """
        query_category = self._detect_query_category(query)

        # If query is general, don't filter
        if query_category == 'general':
            return results

        # Filter documents by matching category
        filtered = []
        for doc, score in results:
            doc_category = doc.metadata.get('category', 'general')
            # Keep if category matches OR if document is general (could be relevant)
            if doc_category == query_category or doc_category == 'general' or doc_category == 'panduan_akademik':
                filtered.append((doc, score))

        return filtered if filtered else results  # Return filtered if non-empty, else original
    
    def _generate_source_label(self, source_file: str) -> str:
        """Generate readable label from filename dynamically (no hardcoding)"""
        # Remove extension
        name = source_file.replace('.md', '').replace('.pdf', '')

        # Clean up filename: replace underscores with spaces
        return name.replace('_', ' ').strip()

    def get_context(self, query: str, top_k: int = None) -> str:
        """Get formatted context string from retrieved documents with clear source labels"""
        results = self.retrieve(query, top_k)

        if not results:
            print(f"[RAG] No results found for query")
            return ""

        # Debug: Print all retrieved chunks
        print(f"\n[RAG DEBUG] Retrieved {len(results)} chunks:")
        for i, (doc, score) in enumerate(results[:5], 1):  # Show top 5
            source = doc.metadata.get('source', 'unknown')
            preview = doc.content[:80].replace('\n', ' ')[:80]
            print(f"  {i}. [{score:.4f}] {source}: {preview}...")

        # Check if top result has very low relevance score (potential hallucination risk)
        top_score = results[0][1]
        if top_score < self.relevance_threshold:
            print(f"[RAG] Warning: Low relevance score ({top_score:.4f} < {self.relevance_threshold}) - refusing to answer")
            return ""  # Return empty context to trigger "not found" response

        context_parts = []
        for i, (doc, score) in enumerate(results, 1):
            source_file = doc.metadata.get('source', 'unknown')
            readable_label = self._generate_source_label(source_file)
            # Include relevance score in context for better LLM judgment
            context_parts.append(f"[SUMBER: {readable_label} | Relevansi: {score:.2f}]\n{doc.content}")

        return "\n\n---\n\n".join(context_parts)
    
    def refresh_index(self):
        """Reload all documents and rebuild index"""
        self.initialize(force_reload=True)
