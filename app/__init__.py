from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config, DATABASE_URL
from .models import db
from .logging_config import setup_logging

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='../static')
    app.config.from_object(Config)
    
    # CORS configuration - Allow Laravel frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8000",          # Laravel dev
                "http://127.0.0.1:8000",          # Laravel dev alt
                "http://localhost:3000",          # Vite dev
                "http://127.0.0.1:3000",          # Vite dev alt
                "https://sinema.fatek.untad.ac.id",  # Production
                "http://sinema.fatek.untad.ac.id",   # Production HTTP
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Database configuration (MySQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    
    # Initialize database
    db.init_app(app)
    
    # Setup logging
    logger = setup_logging(app)
    
    # Initialize rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[Config.RATELIMIT_DEFAULT],
            storage_uri=Config.RATELIMIT_STORAGE_URL
        )
        app.limiter = limiter
        logger.info("Rate limiting initialized")
    except ImportError:
        logger.warning("flask-limiter not installed, rate limiting disabled")
        app.limiter = None
    
    with app.app_context():
        db.create_all()
        # Seed default categories
        from .database import DatabaseService
        DatabaseService.seed_default_categories()
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({
            'error': 'Rate limit exceeded. Please wait before making more requests.',
            'retry_after': error.description
        }), 429
    
    logger.info("Application initialized successfully with CORS enabled")
    return app

