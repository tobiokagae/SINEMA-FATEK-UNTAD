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

        # Re-rank by cosine similarity — highest first
        if results:
            results.sort(key=lambda x: x[1], reverse=True)

        # Filter chunks below relevance threshold
        if results:
            before_count = len(results)
            results = [(doc, score) for doc, score in results if score >= self.relevance_threshold]
            filtered_count = before_count - len(results)
            if filtered_count > 0:
                print(f"[THRESHOLD FILTER] Removed {filtered_count} chunks below threshold ({self.relevance_threshold})")

        # SINEMA boost: dokumen SINEMA sangat kecil (~5 chunk dari 1260+)
        # sehingga sering tidak masuk TOP_K. Boost khusus SINEMA saja.
        if results:
            results = self._boost_sinema(query, expanded_query, results)

        return results

    # Keywords yang menunjukkan query terkait SINEMA
    SINEMA_KEYWORDS = [
        'sinema', 'dashboard', 'login sinema',
    ]

    def _boost_sinema(self, query: str, expanded_query: str, results):
        """
        Boost khusus untuk SINEMA — satu-satunya dokumen yang sangat
        underrepresented (~5 chunk dari 1260+). Jika query menyebut
        keyword SINEMA, pastikan semua chunk SINEMA masuk ke hasil.
        """
        query_lower = query.lower()
        
        # Cek apakah query terkait SINEMA
        if not any(kw in query_lower for kw in self.SINEMA_KEYWORDS):
            return results
        
        # Hitung chunk SINEMA yang sudah ada di results
        existing_sinema = set()
        for doc, _ in results:
            if doc.metadata.get('source', '').upper().startswith('SINEMA'):
                existing_sinema.add(id(doc))
        
        # Ambil semua chunk SINEMA yang belum ada di results
        missing_sinema = [
            doc for doc in self.vector_store.documents
            if doc.metadata.get('source', '').upper().startswith('SINEMA')
            and id(doc) not in existing_sinema
        ]
        
        if not missing_sinema:
            return results  # Semua chunk SINEMA sudah ada
        
        # Hitung similarity score untuk chunk yang missing
        import numpy as np
        try:
            import faiss as _faiss
        except ImportError:
            import faiss_cpu as _faiss
        
        query_emb = self.vector_store.embedding_model.embed_text(expanded_query)
        query_emb = query_emb.reshape(1, -1)
        _faiss.normalize_L2(query_emb)
        
        scored = []
        for doc in missing_sinema:
            doc_emb = self.vector_store.embedding_model.embed_text(doc.content)
            doc_emb = doc_emb.reshape(1, -1)
            _faiss.normalize_L2(doc_emb)
            sim = float(np.dot(query_emb[0], doc_emb[0]))
            scored.append((doc, sim))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Interleave di posisi awal (2, 4, 6, ...) 
        merged = list(results)
        for idx, (doc, score) in enumerate(scored):
            pos = min(2 + idx * 2, len(merged))
            merged.insert(pos, (doc, score))
        
        print(f"[SINEMA BOOST] Added {len(scored)} SINEMA chunks into results")
        
        # Cap di TOP_K
        return merged[:self.top_k]

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
            'seminar tingkat universitas': ['kegiatan forum ilmiah lokakarya workshop pameran poster bobot nilai'],
            'asisten praktikum': ['asisten matakuliah praktikum laboratorium lapang mentor bobot nilai'],
            'mengumpulkan poin': ['klaim ekstrakurikuler pengajuan'],
            'poin': ['bobot nilai ekstrakurikuler kegiatan spe satuan'],
            'ekstrakurikuler': ['kegiatan kemahasiswaan organisasi lomba'],
            'klaim': ['pengajuan bukti sertifikat'],
            'bukti kegiatan': ['sertifikat piagam plakat surat keputusan'],
            'sinema': ['sistem informasi ekstrakurikuler mahasiswa pengajuan klaim'],
        }

        # Check if query matches any expansion pattern (allow multiple matches)
        applied = False
        for pattern, synonyms in expansions.items():
            if pattern in query_lower:
                expanded_query = expanded_query + ' ' + ' '.join(synonyms)
                applied = True

        if applied:
            print(f"[QUERY EXPANSION] '{query}' -> '{expanded_query[:100]}...'")

        return expanded_query



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
