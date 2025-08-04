"""
Flask application factory and configuration.

This module creates and configures the Flask application with all necessary
components including database, routes, and error handlers.
"""

import logging
import os
from typing import Optional

from flask import Flask, render_template, request, g
from werkzeug.exceptions import HTTPException

from ..config import get_config
from ..models import db, UserSettings
from ..services import FinancialDataService


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production')
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters and globals
    register_template_helpers(app)
    
    # Setup request handlers
    setup_request_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default user settings if they don't exist
        default_settings = db.session.query(UserSettings).filter(
            UserSettings.user_id == 'default'
        ).first()
        
        if not default_settings:
            default_settings = UserSettings.get_default_settings()
            db.session.add(default_settings)
            db.session.commit()
    
    return app


def setup_logging(app: Flask) -> None:
    """Setup application logging."""
    if not app.debug and not app.testing:
        # Setup file logging for production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/financial_tracker.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Financial Tracker startup')


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    from .routes import main_bp, accounts_bp, transactions_bp, stocks_bp, settings_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.register_blueprint(stocks_bp, url_prefix='/stocks')
    app.register_blueprint(settings_bp, url_prefix='/settings')


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return render_template('errors/generic.html', error=error), error.code


def register_template_helpers(app: Flask) -> None:
    """Register template filters and global functions."""
    
    @app.template_filter('currency')
    def currency_filter(amount, currency_symbol='$'):
        """Format amount as currency."""
        if amount is None:
            return f"{currency_symbol}0.00"
        return f"{currency_symbol}{amount:,.2f}"
    
    @app.template_filter('abs')
    def abs_filter(value):
        """Get absolute value."""
        return abs(value) if value is not None else 0
    
    @app.template_filter('percentage')
    def percentage_filter(value, decimal_places=2):
        """Format value as percentage."""
        if value is None:
            return "0.00%"
        return f"{value:.{decimal_places}f}%"

    @app.template_filter('number')
    def number_filter(value, decimal_places=None):
        """Format number with thousands separators."""
        if value is None:
            return "0"
        if decimal_places is not None:
            return f"{value:,.{decimal_places}f}"
        # Auto-detect if we need decimal places
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return f"{int(value):,}"
        return f"{value:,.6f}".rstrip('0').rstrip('.')
    
    @app.template_global()
    def get_user_settings():
        """Get current user settings."""
        return getattr(g, 'user_settings', None)
    
    @app.template_global()
    def get_theme_class():
        """Get CSS theme class."""
        settings = get_user_settings()
        if settings:
            return settings.get_theme_css_class()
        return 'theme-light'


def setup_request_handlers(app: Flask) -> None:
    """Setup request handlers for loading user settings."""
    
    @app.before_request
    def load_user_settings():
        """Load user settings before each request."""
        try:
            g.user_settings = db.session.query(UserSettings).filter(
                UserSettings.user_id == 'default'
            ).first()
            
            if not g.user_settings:
                g.user_settings = UserSettings.get_default_settings()
                db.session.add(g.user_settings)
                db.session.commit()
                
        except Exception as e:
            app.logger.error(f"Error loading user settings: {e}")
            g.user_settings = UserSettings.get_default_settings()
    
    @app.before_request
    def setup_financial_data_service():
        """Setup financial data service for the request."""
        try:
            g.financial_data_service = FinancialDataService(
                yfinance_timeout=app.config.get('YFINANCE_TIMEOUT', 10),
                stockdx_api_key=app.config.get('STOCKDX_API_KEY')
            )
        except Exception as e:
            app.logger.error(f"Error setting up financial data service: {e}")
            g.financial_data_service = None


# Utility functions for routes
def get_current_user_settings() -> UserSettings:
    """Get current user settings from request context."""
    return getattr(g, 'user_settings', UserSettings.get_default_settings())


def get_financial_data_service() -> Optional[FinancialDataService]:
    """Get financial data service from request context."""
    return getattr(g, 'financial_data_service', None)


def flash_success(message: str) -> None:
    """Flash a success message."""
    from flask import flash
    flash(message, 'success')


def flash_error(message: str) -> None:
    """Flash an error message."""
    from flask import flash
    flash(message, 'error')


def flash_warning(message: str) -> None:
    """Flash a warning message."""
    from flask import flash
    flash(message, 'warning')


def flash_info(message: str) -> None:
    """Flash an info message."""
    from flask import flash
    flash(message, 'info')
