"""
Settings routes for the Financial Tracker application.

This module handles user settings and preferences management.
"""

import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash

from ...models import db, UserSettings
from ..app import get_current_user_settings, flash_success, flash_error

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
def view_settings():
    """
    View current user settings.
    
    Returns:
        Rendered settings view template
    """
    try:
        settings = get_current_user_settings()
        
        return render_template(
            'settings/view.html',
            settings=settings
        )
        
    except Exception as e:
        logger.error(f"Error viewing settings: {e}")
        flash_error("Unable to load settings. Please try again.")
        return render_template(
            'settings/view.html',
            settings=UserSettings.get_default_settings()
        )


@settings_bp.route('/edit', methods=['GET', 'POST'])
def edit_settings():
    """
    Edit user settings.
    
    Returns:
        GET: Rendered settings edit form
        POST: Redirect to settings view or form with errors
    """
    try:
        settings = get_current_user_settings()
        
        if request.method == 'GET':
            return render_template(
                'settings/form.html',
                settings=settings
            )
        
        # Handle POST request
        theme = request.form.get('theme', 'light').strip()
        currency = request.form.get('currency', '$').strip()
        date_format = request.form.get('date_format', '%Y-%m-%d').strip()
        number_format = request.form.get('number_format', 'en_US').strip()
        financial_period_start_day = request.form.get('financial_period_start_day', 1, type=int)
        transactions_per_page = request.form.get('transactions_per_page', 25, type=int)
        stocks_per_page = request.form.get('stocks_per_page', 20, type=int)
        enable_notifications = request.form.get('enable_notifications') == 'on'
        auto_categorize = request.form.get('auto_categorize') == 'on'
        backup_frequency = request.form.get('backup_frequency', 'weekly').strip()
        language = request.form.get('language', 'en').strip()
        timezone = request.form.get('timezone', 'UTC').strip()
        
        # Validate inputs
        errors = []
        
        if theme not in ['light', 'dark']:
            errors.append("Invalid theme selection.")
        
        if not currency:
            errors.append("Currency symbol is required.")
        
        if financial_period_start_day < 1 or financial_period_start_day > 31:
            errors.append("Financial period start day must be between 1 and 31.")
        
        if transactions_per_page < 5 or transactions_per_page > 100:
            errors.append("Transactions per page must be between 5 and 100.")
        
        if stocks_per_page < 5 or stocks_per_page > 100:
            errors.append("Stocks per page must be between 5 and 100.")
        
        if backup_frequency not in ['daily', 'weekly', 'monthly', 'never']:
            errors.append("Invalid backup frequency.")
        
        if errors:
            for error in errors:
                flash_error(error)
            return render_template(
                'settings/form.html',
                settings=settings
            )
        
        # Update settings
        settings.theme = theme
        settings.currency = currency
        settings.date_format = date_format
        settings.number_format = number_format
        settings.financial_period_start_day = financial_period_start_day
        settings.transactions_per_page = transactions_per_page
        settings.stocks_per_page = stocks_per_page
        settings.enable_notifications = enable_notifications
        settings.auto_categorize = auto_categorize
        settings.backup_frequency = backup_frequency
        settings.language = language
        settings.timezone = timezone
        
        db.session.commit()
        
        flash_success("Settings updated successfully.")
        return redirect(url_for('settings.view_settings'))
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        flash_error("Failed to update settings. Please try again.")
        return redirect(url_for('settings.view_settings'))


@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """
    Reset settings to default values.
    
    Returns:
        Redirect to settings view
    """
    try:
        settings = get_current_user_settings()
        
        # Reset to default values
        default_settings = UserSettings.get_default_settings()
        
        settings.theme = default_settings.theme
        settings.currency = default_settings.currency
        settings.date_format = default_settings.date_format
        settings.number_format = default_settings.number_format
        settings.financial_period_start_day = default_settings.financial_period_start_day
        settings.transactions_per_page = default_settings.transactions_per_page
        settings.stocks_per_page = default_settings.stocks_per_page
        settings.enable_notifications = default_settings.enable_notifications
        settings.auto_categorize = default_settings.auto_categorize
        settings.backup_frequency = default_settings.backup_frequency
        settings.language = default_settings.language
        settings.timezone = default_settings.timezone
        
        db.session.commit()
        
        flash_success("Settings reset to default values.")
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        flash_error("Failed to reset settings. Please try again.")
    
    return redirect(url_for('settings.view_settings'))


@settings_bp.route('/export')
def export_data():
    """
    Export user data (placeholder for future implementation).
    
    Returns:
        Rendered export page
    """
    return render_template(
        'settings/export.html',
        settings=get_current_user_settings()
    )


@settings_bp.route('/import', methods=['GET', 'POST'])
def import_data():
    """
    Import user data (placeholder for future implementation).
    
    Returns:
        GET: Rendered import form
        POST: Process import
    """
    if request.method == 'GET':
        return render_template(
            'settings/import.html',
            settings=get_current_user_settings()
        )
    
    # Placeholder for import functionality
    flash_error("Data import functionality is not yet implemented.")
    return redirect(url_for('settings.view_settings'))


@settings_bp.route('/backup')
def backup_data():
    """
    Create data backup (placeholder for future implementation).
    
    Returns:
        JSON response or file download
    """
    flash_error("Data backup functionality is not yet implemented.")
    return redirect(url_for('settings.view_settings'))


@settings_bp.route('/about')
def about():
    """
    Show application information.
    
    Returns:
        Rendered about page
    """
    return render_template(
        'settings/about.html',
        settings=get_current_user_settings()
    )
