"""
Main Flask application factory
"""
import os
import logging
from flask import Flask, render_template
from flask_cors import CORS
from flask_session import Session

from config import config
from api import auth_bp, sites_bp, files_bp
from utils.logging_config import setup_logging


def create_app(config_name=None):
    """
    Create and configure the Flask application

    Args:
        config_name: Configuration name (development, production)

    Returns:
        Configured Flask application
    """
    # Determine config
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Create Flask app
    app = Flask(__name__,
                static_folder='../frontend/static',
                template_folder='../frontend/templates')

    # Load configuration
    app.config.from_object(config[config_name])

    # Setup logging
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting QC Tool Web Application in {config_name} mode")

    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    Session(app)

    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(sites_bp, url_prefix='/api/sites')
    app.register_blueprint(files_bp, url_prefix='/api/files')

    # Main routes
    @app.route('/')
    def index():
        """Serve login page"""
        return render_template('login.html')

    @app.route('/sites')
    def sites():
        """Serve site selection page"""
        return render_template('sites.html')

    @app.route('/viewer')
    def viewer():
        """Serve file viewer page"""
        return render_template('viewer.html')

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy', 'version': '2.0.0'}, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}", exc_info=True)
        return {'error': 'Internal server error'}, 500

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
