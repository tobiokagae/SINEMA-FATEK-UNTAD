# -*- coding: utf-8 -*-
"""Database models using SQLAlchemy - MySQL Version"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Session(db.Model):
    """Chat session"""
    __tablename__ = 'sessions_chatbot'
    
    id = db.Column(db.String(50), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'message_count': self.messages.count()
        }


class Message(db.Model):
    """Chat message (log_chatbot)"""
    __tablename__ = 'log_chatbot'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(50), db.ForeignKey('sessions_chatbot.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, default=list)  # List of source documents
    latency = db.Column(db.Float, nullable=True)
    cached = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'sources': self.sources or [],
            'latency': self.latency,
            'cached': self.cached,
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }


# NOTE: Feedback model removed - table not created in MySQL


class CacheEntry(db.Model):
    """Semantic cache entries"""
    __tablename__ = 'cache_chatbot'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, default=list)
    latency = db.Column(db.Float, nullable=True)
    hits = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'query': self.query,
            'response': self.response,
            'sources': self.sources or [],
            'latency': self.latency,
            'hits': self.hits
        }


class DailyStats(db.Model):
    """Daily usage statistics"""
    __tablename__ = 'daily_stats_chatbot'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    total_queries = db.Column(db.Integer, default=0)
    cache_hits = db.Column(db.Integer, default=0)
    positive_feedback = db.Column(db.Integer, default=0)
    negative_feedback = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'total_queries': self.total_queries,
            'cache_hits': self.cache_hits,
            'positive_feedback': self.positive_feedback,
            'negative_feedback': self.negative_feedback
        }


class Category(db.Model):
    """Document category for organizing knowledge base"""
    __tablename__ = 'categories_document'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='📄')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = db.relationship('Document', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'icon': self.icon,
            'document_count': self.documents.count()
        }


class Document(db.Model):
    """Document metadata for knowledge base"""
    __tablename__ = 'documents_chatbot'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    original_name = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories_document.id'), nullable=True)
    file_size = db.Column(db.Integer, default=0)
    chunk_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    indexed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_name': self.original_name,
            'category': self.category.to_dict() if self.category else None,
            'file_size': self.file_size,
            'chunk_count': self.chunk_count,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None
        }


class ExpertEvaluation(db.Model):
    """Expert evaluation for chatbot responses"""
    __tablename__ = 'expert_evaluations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expert_name = db.Column(db.String(100), nullable=False, index=True)
    expert_jabatan = db.Column(db.String(200), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    score_akurasi = db.Column(db.Integer, nullable=False)
    score_relevansi = db.Column(db.Integer, nullable=False)
    score_kejelasan = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        scores = {
            'akurasi': self.score_akurasi,
            'relevansi': self.score_relevansi,
            'kejelasan': self.score_kejelasan,
        }
        return {
            'id': self.id,
            'expert_name': self.expert_name,
            'expert_jabatan': self.expert_jabatan or '',
            'category': '',
            'question': self.question,
            'answer': self.answer or '',
            'sources': [],
            'latency': 0,
            'scores': scores,
            'comment': self.comment or '',
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }
