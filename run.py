# -*- coding: utf-8 -*-
"""Entry point for SINEMA RAG Chatbot"""
from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 SINEMA RAG Chatbot - Universitas Tadulako")
    print("=" * 60)
    print(f"Starting server at http://localhost:{Config.PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
