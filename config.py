"""
🎫 Sistema de Tickets - Configuración del Backend
Configuración basada en las especificaciones del README.MD
"""

import os
from datetime import timedelta
from decouple import config

class Config:
    """Base configuration class"""
    
    # Database Configuration
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default=3306, cast=int)
    DB_USER = config('DB_USER', default='root')
    DB_PASSWORD = config('DB_PASSWORD', default='1234')
    DB_NAME = config('DB_NAME', default='tickets_db')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 10,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='your-super-secret-jwt-key-change-in-production-12345')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=config('JWT_ACCESS_TOKEN_EXPIRES', default=900, cast=int))  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=config('JWT_REFRESH_TOKEN_EXPIRES', default=604800, cast=int))  # 7 days
    JWT_ALGORITHM = 'HS256'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Flask Configuration
    SECRET_KEY = config('SECRET_KEY', default='your-super-secret-flask-key-12345')
    DEBUG = config('FLASK_DEBUG', default=True, cast=bool)
    FLASK_ENV = config('FLASK_ENV', default='development')
    
    # Redis Configuration (for sessions and caching)
    REDIS_HOST = config('REDIS_HOST', default='localhost')
    REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
    REDIS_DB = config('REDIS_DB', default=0, cast=int)
    REDIS_PASSWORD = config('REDIS_PASSWORD', default=None)
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = config('MAX_CONTENT_LENGTH', default=5242880, cast=int)  # 5MB
    UPLOAD_FOLDER = config('UPLOAD_FOLDER', default='uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = config('RATELIMIT_STORAGE_URL', default='memory://')
    RATELIMIT_DEFAULT = "100 per minute"
    
    # CORS Configuration
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3001',
        'http://localhost:5173'
    ]
    
    # Security Configuration
    BCRYPT_LOG_ROUNDS = 12
    PASSWORD_MIN_LENGTH = 8
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Payment Configuration (placeholders)
    STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
    STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
    
    # QR Code Configuration
    QR_CODE_SIZE = 10
    QR_CODE_BORDER = 4
    
    # Email Configuration (for future email verification)
    MAIL_SERVER = config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = True
    MAIL_USERNAME = config('MAIL_USERNAME', default='')
    MAIL_PASSWORD = config('MAIL_PASSWORD', default='')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    BCRYPT_LOG_ROUNDS = 4  # Faster for development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    BCRYPT_LOG_ROUNDS = 13  # More secure for production
    
    # Override with environment variables in production
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default=Config.SQLALCHEMY_DATABASE_URI)
    REDIS_URL = config('REDIS_URL', default=Config.REDIS_URL)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=2)

# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
