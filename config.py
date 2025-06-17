import os
from urllib.parse import urlparse

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_secret_key_123'
    API_KEY = os.environ.get('API_KEY') or 'my_secure_key_123'
    BASE_DOMAIN = os.environ.get('BASE_DOMAIN') or 'your-app-name.herokuapp.com'
    
    # Flask settings
    DEBUG = True
    TESTING = True
    
    # Request timeout settings
    REQUEST_TIMEOUT = 10
    MAX_SEARCH_RESULTS = 1
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    BASE_DOMAIN = 'localhost:5000'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class HerokuConfig(ProductionConfig):
    """Heroku-specific configuration"""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Handle proxy headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}
