"""
Web routes package.

This module imports and exposes all route blueprints for the application.
"""

from .main import main_bp
from .accounts import accounts_bp
from .transactions import transactions_bp
from .stocks import stocks_bp
from .settings import settings_bp

__all__ = [
    'main_bp',
    'accounts_bp',
    'transactions_bp',
    'stocks_bp',
    'settings_bp',
]
