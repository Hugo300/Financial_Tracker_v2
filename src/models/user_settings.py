"""
User Settings model for the Financial Tracker application.

This module defines the UserSettings model for managing user preferences and configuration.
"""

from typing import Optional

from sqlalchemy import Column, String, Integer, Boolean, Text

from .base import BaseModel


class UserSettings(BaseModel):
    """
    Model representing user settings and preferences.
    
    Attributes:
        user_id: User identifier (for future multi-user support)
        theme: UI theme preference (light, dark)
        currency: Default currency symbol
        date_format: Preferred date format
        number_format: Preferred number format
        financial_period_start_day: Day of month when financial period starts
        transactions_per_page: Number of transactions to show per page
        stocks_per_page: Number of stocks to show per page
        enable_notifications: Whether to enable notifications
        auto_categorize: Whether to enable automatic transaction categorization
        backup_frequency: How often to backup data
        language: Preferred language
        timezone: User's timezone
        custom_categories: JSON string of custom categories
        dashboard_widgets: JSON string of dashboard widget preferences
    """
    
    __tablename__ = 'user_settings'
    
    user_id = Column(String(50), nullable=False, default='default', index=True)
    theme = Column(String(20), nullable=False, default='light')
    currency = Column(String(3), nullable=False, default='$')
    date_format = Column(String(20), nullable=False, default='%Y-%m-%d')
    number_format = Column(String(20), nullable=False, default='en_US')
    financial_period_start_day = Column(Integer, nullable=False, default=1)
    transactions_per_page = Column(Integer, nullable=False, default=25)
    stocks_per_page = Column(Integer, nullable=False, default=20)
    enable_notifications = Column(Boolean, nullable=False, default=True)
    auto_categorize = Column(Boolean, nullable=False, default=False)
    backup_frequency = Column(String(20), nullable=False, default='weekly')
    language = Column(String(10), nullable=False, default='en')
    timezone = Column(String(50), nullable=False, default='UTC')
    custom_categories = Column(Text)  # JSON string
    dashboard_widgets = Column(Text)  # JSON string
    
    def __init__(
        self,
        user_id: str = 'default',
        theme: str = 'light',
        currency: str = '$',
        date_format: str = '%Y-%m-%d',
        number_format: str = 'en_US',
        financial_period_start_day: int = 1,
        transactions_per_page: int = 25,
        stocks_per_page: int = 20,
        enable_notifications: bool = True,
        auto_categorize: bool = False,
        backup_frequency: str = 'weekly',
        language: str = 'en',
        timezone: str = 'UTC',
        custom_categories: Optional[str] = None,
        dashboard_widgets: Optional[str] = None
    ):
        """
        Initialize new UserSettings.
        
        Args:
            user_id: User identifier
            theme: UI theme preference
            currency: Default currency symbol
            date_format: Preferred date format
            number_format: Preferred number format
            financial_period_start_day: Day of month when financial period starts
            transactions_per_page: Transactions per page
            stocks_per_page: Stocks per page
            enable_notifications: Enable notifications
            auto_categorize: Enable automatic categorization
            backup_frequency: Backup frequency
            language: Preferred language
            timezone: User's timezone
            custom_categories: Custom categories JSON
            dashboard_widgets: Dashboard widgets JSON
        """
        self.user_id = user_id
        self.theme = theme
        self.currency = currency
        self.date_format = date_format
        self.number_format = number_format
        self.financial_period_start_day = financial_period_start_day
        self.transactions_per_page = transactions_per_page
        self.stocks_per_page = stocks_per_page
        self.enable_notifications = enable_notifications
        self.auto_categorize = auto_categorize
        self.backup_frequency = backup_frequency
        self.language = language
        self.timezone = timezone
        self.custom_categories = custom_categories
        self.dashboard_widgets = dashboard_widgets
    
    @classmethod
    def get_default_settings(cls) -> 'UserSettings':
        """
        Get default user settings.
        
        Returns:
            UserSettings instance with default values
        """
        return cls()
    
    def update_setting(self, key: str, value) -> None:
        """
        Update a specific setting.
        
        Args:
            key: Setting key to update
            value: New value for the setting
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise ValueError(f"Invalid setting key: {key}")
    
    def get_theme_css_class(self) -> str:
        """
        Get CSS class for the current theme.
        
        Returns:
            CSS class name for the theme
        """
        return f"theme-{self.theme}"
    
    def is_dark_theme(self) -> bool:
        """
        Check if dark theme is enabled.
        
        Returns:
            True if dark theme is enabled
        """
        return self.theme == 'dark'
    
    def __repr__(self) -> str:
        """String representation of user settings."""
        return f"<UserSettings(id={self.id}, user_id='{self.user_id}', theme='{self.theme}')>"
