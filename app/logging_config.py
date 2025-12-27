# -*- coding: utf-8 -*-
"""Logging configuration for SINEMA Chatbot"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Configure logging for the Flask application"""
    
    # Create logs directory
    log_dir = Path(app.root_path).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_dir / "sinema.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Also configure werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(file_handler)
    
    app.logger.info("Logging initialized")
    
    return app.logger
