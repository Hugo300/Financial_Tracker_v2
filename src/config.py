"""
Configuration module for the Financial Tracker application.

This module handles application configuration including environment variables,
database settings, and application defaults.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    # Flask settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or 'sqlite:///financial_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Application settings
    APP_NAME: str = "Financial Tracker"
    APP_VERSION: str = "0.1.0"

    # Address and port
    FLASK_HOST: str = '127.0.0.1'
    FLASK_PORT: int = 5000
    
    # Financial API settings
    YFINANCE_TIMEOUT: int = int(os.environ.get('YFINANCE_TIMEOUT', '10'))
    STOCKDEX_API_KEY: Optional[str] = os.environ.get('STOCKDEX_API_KEY')
    STOCKDEX_TIMEOUT: int = int(os.environ.get('STOCKDEX_TIMEOUT', '10'))
    
    # UI settings
    DEFAULT_THEME: str = os.environ.get('DEFAULT_THEME', 'light')
    DEFAULT_CURRENCY: str = os.environ.get('DEFAULT_CURRENCY', '$')
    
    # Pagination settings
    TRANSACTIONS_PER_PAGE: int = int(os.environ.get('TRANSACTIONS_PER_PAGE', '25'))
    STOCKS_PER_PAGE: int = int(os.environ.get('STOCKS_PER_PAGE', '20'))
    
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    ALLOWED_EXTENSIONS: set = {'csv', 'txt'}


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    
    DEBUG: bool = True
    TESTING: bool = False
    
    # Use in-memory database for development if specified
    if os.environ.get('USE_MEMORY_DB'):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Address and port
    FLASK_HOST: str = '127.0.0.1'
    FLASK_PORT: int = 5000


class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    
    DEBUG: bool = False
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'

    # Address and port
    FLASK_HOST: str = '127.0.0.1'
    FLASK_PORT: int = 5005


class ProductionConfig(Config):
    """Production configuration with enhanced security."""
    
    DEBUG: bool = False
    TESTING: bool = False
    
    # Ensure secret key is set in production
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set in production")


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration object based on environment.
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable or 'default'
    
    Returns:
        Configuration object instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config_map.get(config_name, DevelopmentConfig)()
