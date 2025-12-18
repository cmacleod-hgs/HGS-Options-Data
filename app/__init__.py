"""
Flask application factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='default'):
    """Create and configure the Flask application"""
    # Set instance path explicitly
    instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance'))
    
    app = Flask(__name__, instance_path=instance_path)
    app.config.from_object(config[config_name])
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.analysis import analysis_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
