# -*- coding: utf-8 -*-
"""Script to migrate existing documents to SQLite database"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.getcwd())

from flask import Flask
from app.config import DATABASE_PATH, DOCUMENTS_DIR
from app.models import db, Category, Document
from app.database import DatabaseService

def create_minimal_app():
    """Create minimal Flask app for database operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def main():
    print("=" * 50)
    print("MIGRATING DOCUMENTS TO DATABASE")
    print("=" * 50)
    
    app = create_minimal_app()
    
    with app.app_context():
        # Create tables
        print("\n1. Creating tables...")
        db.create_all()
        
        # Seed categories
        print("\n2. Seeding categories...")
        DatabaseService.seed_default_categories()
        
        # Show categories
        categories = DatabaseService.get_all_categories()
        print(f"   Created {len(categories)} categories:")
        for cat in categories:
            print(f"   - {cat['icon']} {cat['display_name']} ({cat['name']})")
        
        # Category mapping based on filename patterns
        CATEGORY_MAP = {
            'panduan_ta': 'panduan_ta',
            'ta_non': 'panduan_ta',
            'tugas_akhir': 'panduan_ta',
            'integritas': 'integritas_akademik',
            'akademik_fatek': 'panduan_akademik',
            'panduan_akademik': 'panduan_akademik',
            'sinema': 'panduan_sinema',
            'ekstrakurikuler': 'panduan_sinema',
            'poin_ekskul': 'panduan_sinema',
            'satuan_poin': 'panduan_sinema'
        }
        
        def get_category_id(filename):
            """Determine category from filename"""
            filename_lower = filename.lower()
            for key, cat_name in CATEGORY_MAP.items():
                if key in filename_lower:
                    cat = DatabaseService.get_category_by_name(cat_name)
                    return cat.id if cat else None
            return None
        
        # Migrate existing documents
        print("\n3. Migrating documents...")
        supported_ext = {'.pdf', '.docx', '.doc', '.txt', '.md'}
        
        docs_dir = Path(DOCUMENTS_DIR)
        if docs_dir.exists():
            for file_path in docs_dir.iterdir():
                if file_path.suffix.lower() in supported_ext:
                    category_id = get_category_id(file_path.name)
                    file_size = file_path.stat().st_size
                    
                    # Estimate chunk count (rough estimate)
                    chunk_count = max(1, file_size // 500)
                    
                    doc = DatabaseService.add_document(
                        filename=file_path.name,
                        category_id=category_id,
                        file_size=file_size,
                        chunk_count=chunk_count,
                        original_name=file_path.name
                    )
                    
                    cat_name = doc.category.display_name if doc.category else "Uncategorized"
                    print(f"   ✅ {file_path.name} -> {cat_name}")
        
        # Show final count
        all_docs = DatabaseService.get_all_documents()
        print(f"\n   Total documents in database: {len(all_docs)}")
        
        print("\n" + "=" * 50)
        print("MIGRATION COMPLETED!")
        print("=" * 50)

if __name__ == "__main__":
    main()
