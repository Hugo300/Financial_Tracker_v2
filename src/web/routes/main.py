"""
Main routes for the Financial Tracker application.

This module handles the dashboard and main navigation routes.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, jsonify

from ...models import db
from ...services import AccountService, TransactionService, StockService
from ..app import get_current_user_settings, get_financial_data_service

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """
    Main dashboard showing financial overview.
    
    Returns:
        Rendered dashboard template
    """
    try:
        # Initialize services
        account_service = AccountService()
        transaction_service = TransactionService()
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        # Get user settings
        settings = get_current_user_settings()
        
        # Get account summary
        account_summary = account_service.get_account_summary()
        
        # Get recent transactions (last 10)
        recent_transactions = transaction_service.get_transactions(limit=10)
        
        # Get transaction summary for current month
        today = date.today()
        month_start = today.replace(day=1)
        transaction_summary = transaction_service.get_transaction_summary(
            start_date=month_start,
            end_date=today
        )
        
        # Get portfolio summary
        portfolio_summary = stock_service.get_portfolio_summary()
        
        # Calculate net worth
        net_worth = account_summary['net_worth'] + portfolio_summary['total_value']
        
        # Get spending by category for chart
        category_spending = transaction_summary.get('category_spending', {})
        
        # Prepare chart data
        chart_data = {
            'categories': list(category_spending.keys()),
            'amounts': [float(amount) for amount in category_spending.values()]
        }
        
        return render_template(
            'dashboard.html',
            account_summary=account_summary,
            transaction_summary=transaction_summary,
            portfolio_summary=portfolio_summary,
            recent_transactions=recent_transactions,
            net_worth=net_worth,
            chart_data=chart_data,
            settings=settings
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template(
            'dashboard.html',
            error="Unable to load dashboard data. Please try again.",
            account_summary={},
            transaction_summary={},
            portfolio_summary={},
            recent_transactions=[],
            net_worth=Decimal('0'),
            chart_data={'categories': [], 'amounts': []},
            settings=get_current_user_settings()
        )


@main_bp.route('/api/dashboard/refresh')
def refresh_dashboard_data():
    """
    API endpoint to refresh dashboard data.
    
    Returns:
        JSON response with updated dashboard data
    """
    try:
        # Initialize services
        account_service = AccountService()
        transaction_service = TransactionService()
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        # Update stock prices
        stock_service.update_all_stock_prices()
        
        # Get updated summaries
        account_summary = account_service.get_account_summary()
        portfolio_summary = stock_service.get_portfolio_summary()
        
        # Calculate net worth
        net_worth = account_summary['net_worth'] + portfolio_summary['total_value']
        
        return jsonify({
            'success': True,
            'data': {
                'net_worth': float(net_worth),
                'total_assets': float(account_summary['total_assets']),
                'total_liabilities': float(account_summary['total_liabilities']),
                'portfolio_value': float(portfolio_summary['total_value']),
                'portfolio_gain_loss': float(portfolio_summary['total_gain_loss']),
                'portfolio_gain_loss_percentage': float(portfolio_summary['total_gain_loss_percentage'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to refresh dashboard data'
        }), 500


@main_bp.route('/api/chart/spending')
def spending_chart_data():
    """
    API endpoint for spending chart data.
    
    Returns:
        JSON response with spending data by category
    """
    try:
        transaction_service = TransactionService()
        
        # Get date range from query parameters
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transaction summary
        summary = transaction_service.get_transaction_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        category_spending = summary.get('category_spending', {})
        
        # Format data for chart
        chart_data = {
            'labels': list(category_spending.keys()),
            'data': [float(amount) for amount in category_spending.values()],
            'total': float(summary.get('total_expenses', 0))
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error getting spending chart data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load chart data'
        }), 500


@main_bp.route('/api/chart/balance-trend')
def balance_trend_data():
    """
    API endpoint for balance trend chart data.
    
    Returns:
        JSON response with balance trend data
    """
    try:
        account_service = AccountService()
        
        # Get account ID from query parameters
        account_id = request.args.get('account_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        if not account_id:
            return jsonify({
                'success': False,
                'error': 'Account ID is required'
            }), 400
        
        # Get balance history
        history = account_service.get_balance_history(account_id, days)
        
        # Format data for chart
        chart_data = {
            'labels': [record['date'].isoformat() for record in history],
            'data': [float(record['balance']) for record in history]
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error getting balance trend data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load balance trend data'
        }), 500


@main_bp.route('/search')
def search():
    """
    Global search functionality.
    
    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': True,
                'results': []
            })
        
        # Initialize services
        transaction_service = TransactionService()
        account_service = AccountService()
        stock_service = StockService()
        
        results = []
        
        # Search transactions
        transactions = transaction_service.get_transactions(limit=5)
        for transaction in transactions:
            if query.lower() in transaction.description.lower():
                results.append({
                    'type': 'transaction',
                    'title': transaction.description,
                    'subtitle': f"{transaction.formatted_amount} on {transaction.date}",
                    'url': f"/transactions/{transaction.id}"
                })
        
        # Search accounts
        accounts = account_service.get_accounts()
        for account in accounts:
            if query.lower() in account.name.lower():
                results.append({
                    'type': 'account',
                    'title': account.name,
                    'subtitle': f"{account.account_type.value} - {account.formatted_balance}",
                    'url': f"/accounts/{account.id}"
                })
        
        # Search stocks
        stocks = stock_service.get_stocks(limit=5)
        for stock in stocks:
            if (query.lower() in stock.symbol.lower() or 
                query.lower() in stock.name.lower()):
                results.append({
                    'type': 'stock',
                    'title': f"{stock.symbol} - {stock.name}",
                    'subtitle': f"Last price: {stock.formatted_price}",
                    'url': f"/stocks/{stock.id}"
                })
        
        return jsonify({
            'success': True,
            'results': results[:10]  # Limit to 10 results
        })
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500
