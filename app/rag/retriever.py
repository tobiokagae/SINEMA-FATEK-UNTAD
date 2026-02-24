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
        top_k: int = 3,
        relevance_threshold: float = 0.3
    ):
        self.documents_dir = Path(documents_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.top_k = top_k
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

        if use_mmr:
            # Use MMR for diverse results (fetch more candidates, return top_k)
            results = self.vector_store.search_mmr(
                expanded_query,  # Use expanded query
                top_k=k,
                fetch_k=k * 3,  # Fetch 3x candidates for better diversity
                lambda_mult=0.7,  # 70% relevance, 30% diversity
                diversity_boost=0.3  # Extra boost for new source documents
            )
        else:
            # Standard similarity search
            results = self.vector_store.search(expanded_query, top_k=k)

        # Apply category-based filtering
        if results:
            results = self._filter_by_category(query, results)
            print(f"[CATEGORY FILTER] After filtering: {len(results)} results")

        # Boost: ensure related category chunks are included
        if results:
            results = self._boost_related_categories(query, expanded_query, results)

        return results

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms, abbreviations, and related terms for better retrieval

        Args:
            query: Original query

        Returns:
            Expanded query with synonyms and expanded abbreviations
        """
        query_lower = query.lower()
        expanded_query = query
        
        # Common academic abbreviations mapping
        abbreviations = {
            'ipk': 'indeks prestasi kumulatif',
            'sks': 'satuan kredit semester',
            'ta': 'tugas akhir',
            'krs': 'kartu rencana studi',
            'khs': 'kartu hasil studi',
            'spe': 'sistem penilaian ekstrakurikuler',
            'kre': 'kartu rencana ekstrakurikuler',
            'khe': 'kartu hasil ekstrakurikuler',
            'tem': 'transkrip ekstrakurikuler mahasiswa',
            'ukm': 'unit kegiatan mahasiswa',
            'ukf': 'unit kegiatan fakultas',
            'hmj': 'himpunan mahasiswa jurusan',
            'hmp': 'himpunan mahasiswa program studi',
            'bem': 'badan eksekutif mahasiswa',
            'dpa': 'dosen pembimbing akademik',
            'mk': 'mata kuliah',
            'uts': 'ujian tengah semester',
            'uas': 'ujian akhir semester',
            'kpm': 'kuliah pengabdian masyarakat',
            'kkn': 'kuliah kerja nyata',
            'ppl': 'praktik pengalaman lapangan',
            'fatek': 'fakultas teknik',
        }
        
        # Expand abbreviations in query
        words = query_lower.split()
        expanded_words = []
        has_abbreviation = False
        
        for word in words:
            # Clean word from punctuation for matching
            clean_word = word.strip('.,?!')
            if clean_word in abbreviations:
                expanded_words.append(f"{word} {abbreviations[clean_word]}")
                has_abbreviation = True
            else:
                expanded_words.append(word)
        
        if has_abbreviation:
            expanded_query = ' '.join(expanded_words)
            print(f"[ABBREV EXPANSION] '{query}' -> '{expanded_query[:80]}...'")

        # Define additional expansion rules for phrases
        expansions = {
            'mengumpulkan poin': ['klaim ekstrakurikuler pengajuan'],
            'poin': ['ekstrakurikuler kegiatan spe'],
            'ekstrakurikuler': ['kegiatan kemahasiswaan organisasi lomba'],
            'klaim': ['pengajuan bukti sertifikat'],
        }

        # Check if query matches any expansion pattern
        for pattern, synonyms in expansions.items():
            if pattern in query_lower:
                expanded_query = expanded_query + ' ' + ' '.join(synonyms)
                print(f"[QUERY EXPANSION] '{query}' -> '{expanded_query[:100]}...'")
                break

        return expanded_query

    def _detect_query_category(self, query: str) -> str:
        """Detect the likely category of a query for better filtering

        Args:
            query: The search query

        Returns:
            Detected category
        """
        query_lower = query.lower()

        # Keyword-based category detection
        if any(word in query_lower for word in ['poin', 'ekstrakurikuler', 'spe', 'lomba', 'organisasi', 'ukm']):
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

    # Related categories that should not be filtered out from each other
    RELATED_CATEGORIES = {
        'poin_ekstrakurikuler': ['website_sinema'],   # SINEMA = tool untuk poin
        'website_sinema': ['poin_ekstrakurikuler'],   # Sebaliknya juga
        'transkrip_tem': ['website_sinema', 'poin_ekstrakurikuler'],  # TEM juga via SINEMA
    }

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

        # Get related categories for this query category
        related = self.RELATED_CATEGORIES.get(query_category, [])

        # Filter documents by matching category + related categories
        filtered = []
        for doc, score in results:
            doc_category = doc.metadata.get('category', 'general')
            # Keep if: category matches OR related category OR general OR panduan_akademik
            if doc_category == query_category or doc_category in related or doc_category == 'general' or doc_category == 'panduan_akademik':
                filtered.append((doc, score))

        return filtered if filtered else results  # Return filtered if non-empty, else original

    def _boost_related_categories(self, query: str, expanded_query: str, results: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        """Ensure related category chunks are included even if FAISS didn't rank them highly.
        
        Small document collections (e.g., SINEMA with only 5 chunks out of 1621) may never
        appear in FAISS top-K results. This method finds and INTERLEAVES them into top
        positions so they are guaranteed to be within TOP_K.
        """
        query_category = self._detect_query_category(query)
        related = self.RELATED_CATEGORIES.get(query_category, [])
        
        # All categories that SHOULD be present: query's own category + related
        desired_categories = [query_category] + related
        
        if not desired_categories or query_category == 'general':
            return results
        
        # Check which desired categories are underrepresented in results
        # A category is "underrepresented" if it has fewer than MIN chunks.
        # Previously we only boosted MISSING categories, but a category with
        # just 1 chunk (out of 5 total) still needs boosting.
        MIN_CATEGORY_CHUNKS = 3
        category_counts = {}
        for doc, _ in results:
            cat = doc.metadata.get('category', '')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        underrepresented = [
            cat for cat in desired_categories
            if category_counts.get(cat, 0) < MIN_CATEGORY_CHUNKS
        ]
        
        if not underrepresented:
            return results  # All desired categories have enough representation
        
        # Find and score chunks from underrepresented categories
        try:
            import numpy as np
            import faiss as _faiss
            
            # Embed the query using same method as VectorStore.search
            query_emb = self.vector_store.embedding_model.embed_text(expanded_query)
            query_emb = query_emb.reshape(1, -1)
            _faiss.normalize_L2(query_emb)
            
            all_boosted = []
            for boost_cat in underrepresented:
                # Collect chunks from this category (exclude already-present ones)
                existing_docs = set(id(doc) for doc, _ in results if doc.metadata.get('category', '') == boost_cat)
                cat_chunks = [
                    doc for doc in self.vector_store.documents
                    if doc.metadata.get('category', '') == boost_cat and id(doc) not in existing_docs
                ]
                if not cat_chunks:
                    continue
                
                # Embed each chunk and compute similarity
                scored = []
                for doc in cat_chunks:
                    doc_emb = self.vector_store.embedding_model.embed_text(doc.content)
                    doc_emb = doc_emb.reshape(1, -1)
                    _faiss.normalize_L2(doc_emb)
                    # Dot product of normalized vectors = cosine similarity
                    sim = float(np.dot(query_emb[0], doc_emb[0]))
                    scored.append((doc, sim))
                
                # Sort by score, take top 5 (include all chunks for small documents like SINEMA)
                scored.sort(key=lambda x: x[1], reverse=True)
                added = scored[:5]
                
                if added:
                    print(f"[CATEGORY BOOST] Added {len(added)} chunks from '{boost_cat}' (scores: {', '.join(f'{s:.4f}' for _, s in added)})")
                    all_boosted.extend(added)
            
            if not all_boosted:
                return results
            
            # INTERLEAVE boosted chunks into top positions instead of appending
            # at the end (where they would be sorted past TOP_K).
            # Strategy: insert boosted chunks at positions 2, 4, 6, 8, 10, ...
            # so they are guaranteed to be within TOP_K results.
            merged = list(results)
            insert_positions = [2, 4, 6, 8, 10]  # Insert at these indices (0-based)
            for idx, (doc, score) in enumerate(all_boosted):
                if idx < len(insert_positions):
                    pos = min(insert_positions[idx], len(merged))
                else:
                    pos = min(12, len(merged))  # Extra boosted go near position 12
                merged.insert(pos, (doc, score))
            
            print(f"[CATEGORY BOOST] Interleaved {len(all_boosted)} boosted chunks into top positions")
            return merged
            
        except Exception as e:
            print(f"[CATEGORY BOOST] Error: {e}")
            return results
    
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

        # Debug: Print all retrieved chunks with keyword highlighting
        print(f"\n[RAG DEBUG] Retrieved {len(results)} chunks:")
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get('source', 'unknown')
            preview = doc.content[:200].replace('\n', ' ')
            # Check for key terms
            content_lower = doc.content.lower()
            has_sks = 'sks' in content_lower
            has_ekstra = 'ekstrakurikuler' in content_lower or 'ekstra' in content_lower
            flags = []
            if has_sks: flags.append('📌SKS')
            if has_ekstra: flags.append('📌EKSTRA')
            flag_str = f" {' '.join(flags)}" if flags else ""
            print(f"  {i}. [{score:.4f}] {source}{flag_str}: {preview}...")

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
