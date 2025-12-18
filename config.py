"""
Configuration settings for the Flask application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # OAuth Configuration
    OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID')
    OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET')
    OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    OAUTH_AUTHORIZATION_URL = os.environ.get('OAUTH_AUTHORIZATION_URL')
    OAUTH_TOKEN_URL = os.environ.get('OAUTH_TOKEN_URL')
    OAUTH_USERINFO_URL = os.environ.get('OAUTH_USERINFO_URL')
    
    # File Upload Configuration
    UPLOAD_FOLDER = str(basedir / 'data' / 'uploads')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database Configuration (SQLite for development)
    # For Windows, SQLite needs 4 slashes before absolute paths
    db_file = basedir / 'instance' / 'app.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{db_file.as_posix()}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
