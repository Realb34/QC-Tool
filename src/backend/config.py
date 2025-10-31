"""
Application configuration
"""
import os
import secrets
from datetime import timedelta

class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Session settings - using Flask's native signed cookie sessions
    # SESSION_TYPE is not needed for Flask's native sessions (only for Flask-Session extension)
    SESSION_PERMANENT = True
    SESSION_COOKIE_NAME = 'qc_tool_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # Same-origin requests (page and API on same domain)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_PATH = '/'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)

    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # FTP/SFTP connection settings
    CONNECTION_TIMEOUT = 30  # seconds
    SESSION_TIMEOUT = 14400  # 4 hours in seconds

    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

    # CORS settings - allow Render URLs and localhost
    default_origins = 'http://localhost:*,https://*.onrender.com'
    CORS_ORIGINS = os.environ.get('ALLOWED_ORIGINS', default_origins).split(',')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # For HTTPS deployments (Render provides HTTPS)
    SESSION_COOKIE_SECURE = True
    # Same-origin requests - Lax is appropriate
    SESSION_COOKIE_SAMESITE = 'Lax'


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
