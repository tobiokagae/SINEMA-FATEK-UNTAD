# -*- coding: utf-8 -*-
"""Database service layer for chat operations - MySQL Version (SQLAlchemy 2.0 compatible)"""
import hashlib
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from .models import db, Session, Message, CacheEntry, DailyStats, Category, Document


class DatabaseService:
    """Service class for all database operations"""
    
    # =========================
    # Session Operations
    # =========================
    
    @staticmethod
    def create_session(session_id: str = None) -> str:
        """Create a new chat session"""
        if session_id is None:
            session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:12]
        
        existing = db.session.get(Session, session_id)
        if existing:
            return session_id
        
        session = Session(id=session_id)
        db.session.add(session)
        db.session.commit()
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return db.session.get(Session, session_id)
    
    @staticmethod
    def get_all_sessions(limit: int = 50) -> List[Dict]:
        """Get all sessions with summary"""
        sessions = db.session.query(Session).order_by(Session.updated_at.desc()).limit(limit).all()
        return [s.to_dict() for s in sessions]
    
    # =========================
    # Message Operations
    # =========================
    
    @staticmethod
    def add_message(session_id: str, role: str, content: str, 
                    sources: List = None, latency: float = None, cached: bool = False) -> Message:
        """Add a message to session"""
        # Ensure session exists
        session = db.session.get(Session, session_id)
        if not session:
            session = Session(id=session_id)
            db.session.add(session)
        
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources or [],
            latency=latency,
            cached=cached
        )
        db.session.add(message)
        
        # Update session timestamp
        session.updated_at = datetime.utcnow()
        
        # Update daily stats
        if role == 'user':
            DatabaseService._increment_daily_queries()
        
        db.session.commit()
        return message
    
    @staticmethod
    def get_messages(session_id: str, limit: int = None) -> List[Dict]:
        """Get messages from session"""
        query = db.session.query(Message).filter_by(session_id=session_id).order_by(Message.created_at.asc())
        if limit:
            query = query.limit(limit)
        return [m.to_dict() for m in query.all()]
    
    @staticmethod
    def get_recent_context(session_id: str, n_turns: int = 3) -> str:
        """Get recent conversation context for multi-turn (legacy method)"""
        messages = db.session.query(Message).filter_by(session_id=session_id)\
            .order_by(Message.created_at.desc())\
            .limit(n_turns * 2).all()
        
        messages.reverse()  # Oldest first
        
        context_parts = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            content = msg.content[:200] if len(msg.content) > 200 else msg.content
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def get_context_sliding_window(session_id: str, recent_turns: int = 2) -> Tuple[List[Dict], List[Dict]]:
        """
        Get conversation context using sliding window approach.
        
        Returns:
            Tuple of (older_messages, recent_messages)
            - older_messages: Messages to be summarized (older than recent_turns)
            - recent_messages: Most recent messages to keep in full
        """
        # Get ALL messages from this session
        all_messages = db.session.query(Message).filter_by(session_id=session_id)\
            .order_by(Message.created_at.asc()).all()
        
        if not all_messages:
            return [], []
        
        # Convert to dict format
        messages_list = []
        for msg in all_messages:
            messages_list.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            })
        
        # Split into older and recent
        # recent_turns * 2 because each turn = 1 user + 1 assistant message
        recent_count = recent_turns * 2
        
        if len(messages_list) <= recent_count:
            # All messages are "recent", nothing to summarize
            return [], messages_list
        
        older_messages = messages_list[:-recent_count]
        recent_messages = messages_list[-recent_count:]
        
        return older_messages, recent_messages
    
    @staticmethod
    def format_messages_for_context(messages: List[Dict], max_chars: int = 300) -> str:
        """Format messages list into context string"""
        context_parts = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Bot"
            content = msg["content"]
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            context_parts.append(f"{role}: {content}")
        return "\n".join(context_parts)
    

    # =========================
    # Cache Operations
    # =========================
    
    @staticmethod
    def get_cache_hash(query: str) -> str:
        """Generate hash for query - normalized (lowercase, no punctuation)"""
        import re
        # Remove punctuation, lowercase, strip whitespace
        normalized = re.sub(r'[^\w\s]', '', query.lower().strip())
        # Collapse multiple spaces into one
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    @staticmethod
    def get_cached_response(query: str) -> Optional[Tuple[str, List, float]]:
        """Get cached response by query"""
        query_hash = DatabaseService.get_cache_hash(query)
        entry = db.session.query(CacheEntry).filter_by(query_hash=query_hash).first()
        
        if entry:
            entry.hits += 1
            DatabaseService._increment_daily_cache_hits()
            db.session.commit()
            return entry.response, entry.sources or [], entry.latency
        
        return None
    
    @staticmethod
    def cache_response(query: str, response: str, sources: List, latency: float):
        """Cache a response if no similar query exists"""
        from flask import current_app
        logger = current_app.logger
        
        query_hash = DatabaseService.get_cache_hash(query)
        logger.info(f"[CACHE] Attempting to cache query: '{query[:50]}...' hash={query_hash[:16]}...")
        
        # Check if exact hash exists
        existing = db.session.query(CacheEntry).filter_by(query_hash=query_hash).first()
        if existing:
            logger.info(f"[CACHE] SKIP - Exact hash already exists")
            return
        
        # Check for semantically similar queries using word overlap
        query_words = set(query.lower().strip().split())
        
        # Get recent cache entries to compare
        recent_entries = db.session.query(CacheEntry).order_by(CacheEntry.created_at.desc()).limit(100).all()
        
        for entry in recent_entries:
            cached_words = set(entry.query.lower().strip().split())
            
            # Calculate Jaccard similarity
            if query_words and cached_words:
                intersection = len(query_words & cached_words)
                union = len(query_words | cached_words)
                similarity = intersection / union if union > 0 else 0
                
                # Skip if too similar (>70% overlap)
                if similarity > 0.7:
                    logger.info(f"[CACHE] SKIP - Similar query exists (sim={similarity:.2f})")
                    return
        
        # Save new cache entry
        try:
            entry = CacheEntry(
                query_hash=query_hash,
                query=query,
                response=response,
                sources=sources,
                latency=latency
            )
            db.session.add(entry)
            db.session.commit()
            logger.info(f"[CACHE] SUCCESS - Saved new cache entry, id={entry.id}")
        except Exception as e:
            logger.error(f"[CACHE] ERROR - Failed to save: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """Get cache statistics"""
        total_entries = db.session.query(CacheEntry).count()
        total_hits = db.session.query(db.func.sum(CacheEntry.hits)).scalar() or 0
        return {
            'entries': total_entries,
            'total_hits': int(total_hits)
        }
    
    @staticmethod
    def clear_all_cache() -> int:
        """Clear all cache entries and reset ID - called when documents change"""
        # Use TRUNCATE to reset AUTO_INCREMENT to 1
        db.session.execute(db.text('TRUNCATE TABLE cache_chatbot'))
        db.session.commit()
        return 0  # TRUNCATE doesn't return row count
    
    @staticmethod
    def get_top_queries(limit: int = 10) -> List[str]:
        """Get most frequently asked questions"""
        entries = db.session.query(CacheEntry).order_by(CacheEntry.hits.desc()).limit(limit).all()
        return [e.query[:50] for e in entries]
    
    # =========================
    # Statistics Operations
    # =========================
    
    @staticmethod
    def _get_or_create_today_stats() -> DailyStats:
        """Get or create today's stats record"""
        today = date.today()
        stats = db.session.query(DailyStats).filter_by(date=today).first()
        
        if not stats:
            stats = DailyStats(
                date=today,
                total_queries=0,
                cache_hits=0,
                positive_feedback=0,
                negative_feedback=0
            )
            db.session.add(stats)
            db.session.flush()  # Ensure the record is created before returning
        
        return stats
    
    @staticmethod
    def _increment_daily_queries():
        """Increment today's query count"""
        stats = DatabaseService._get_or_create_today_stats()
        stats.total_queries += 1
    
    @staticmethod
    def _increment_daily_cache_hits():
        """Increment today's cache hit count"""
        stats = DatabaseService._get_or_create_today_stats()
        stats.cache_hits += 1
    
    @staticmethod
    def get_admin_stats() -> Dict:
        """Get comprehensive admin statistics"""
        total_sessions = db.session.query(Session).count()
        total_messages = db.session.query(Message).count()
        
        # Today's stats
        today = date.today()
        today_stats = db.session.query(DailyStats).filter_by(date=today).first()
        today_queries = today_stats.total_queries if today_stats else 0
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'today_questions': today_queries,
            'cache': DatabaseService.get_cache_stats(),
            'top_queries': DatabaseService.get_top_queries(5)
        }
    
    # =========================
    # Category Operations
    # =========================
    
    @staticmethod
    def get_all_categories() -> List[Dict]:
        """Get all document categories"""
        categories = db.session.query(Category).order_by(Category.name).all()
        return [c.to_dict() for c in categories]
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional[Category]:
        """Get category by name"""
        return db.session.query(Category).filter_by(name=name).first()
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return db.session.get(Category, category_id)
    
    @staticmethod
    def create_category(name: str, display_name: str, icon: str = '📁') -> Optional[Category]:
        """Create a new category"""
        try:
            category = Category(name=name, display_name=display_name, icon=icon)
            db.session.add(category)
            db.session.commit()
            return category
        except Exception as e:
            db.session.rollback()
            return None
    
    @staticmethod
    def seed_default_categories():
        """Seed default document categories"""
        default_categories = [
            {'name': 'panduan_ta', 'display_name': 'Panduan Tugas Akhir', 'icon': '📚'},
            {'name': 'integritas_akademik', 'display_name': 'Integritas Akademik', 'icon': '⚖️'},
            {'name': 'panduan_akademik', 'display_name': 'Panduan Akademik FATEK', 'icon': '🎓'},
            {'name': 'panduan_sinema', 'display_name': 'Panduan SINEMA/Poin Ekskul', 'icon': '🌐'}
        ]
        
        for cat_data in default_categories:
            existing = db.session.query(Category).filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
        
        db.session.commit()
    
    # =========================
    # Document Operations
    # =========================
    
    @staticmethod
    def add_document(filename: str, category_id: int = None, file_size: int = 0, 
                     chunk_count: int = 0, original_name: str = None) -> Document:
        """Add a document to the database"""
        # Check if exists
        existing = db.session.query(Document).filter_by(filename=filename).first()
        if existing:
            # Update existing
            existing.category_id = category_id
            existing.file_size = file_size
            existing.chunk_count = chunk_count
            existing.indexed_at = datetime.utcnow()
            db.session.commit()
            return existing
        
        doc = Document(
            filename=filename,
            original_name=original_name or filename,
            category_id=category_id,
            file_size=file_size,
            chunk_count=chunk_count,
            indexed_at=datetime.utcnow()
        )
        db.session.add(doc)
        db.session.commit()
        return doc
    
    @staticmethod
    def get_all_documents() -> List[Dict]:
        """Get all documents"""
        docs = db.session.query(Document).order_by(Document.uploaded_at.desc()).all()
        return [d.to_dict() for d in docs]
    
    @staticmethod
    def get_documents_by_category(category_id: int) -> List[Dict]:
        """Get documents by category"""
        docs = db.session.query(Document).filter_by(category_id=category_id).all()
        return [d.to_dict() for d in docs]
    
    @staticmethod
    def delete_document(document_id: int) -> bool:
        """Delete a document by ID"""
        doc = db.session.get(Document, document_id)
        if doc:
            db.session.delete(doc)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_document_by_filename(filename: str) -> Optional[Document]:
        """Get document by filename"""
        return db.session.query(Document).filter_by(filename=filename).first()
    
    @staticmethod
    def delete_document_by_filename(filename: str) -> bool:
        """Delete a document by filename"""
        from flask import current_app
        try:
            doc = db.session.query(Document).filter_by(filename=filename).first()
            if doc:
                current_app.logger.info(f"Found document to delete: id={doc.id}, filename={doc.filename}")
                db.session.delete(doc)
                db.session.commit()
                current_app.logger.info(f"Successfully deleted document: {filename}")
                return True
            else:
                current_app.logger.warning(f"Document not found for deletion: {filename}")
                return False
        except Exception as e:
            current_app.logger.error(f"Error deleting document {filename}: {e}")
            db.session.rollback()
            return False
