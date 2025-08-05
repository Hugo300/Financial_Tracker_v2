"""
Stock routes for the Financial Tracker application.

This module handles stock and portfolio management including
stock tracking, holdings, and investment analytics.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from ...models import StockTransactionType, AccountType
from ...services import StockService, AccountService
from ..app import get_current_user_settings, get_financial_data_service, flash_success, flash_error

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__)


@stocks_bp.route('/')
def list_stocks():
    """
    List all stocks and portfolio overview.
    
    Returns:
        Rendered stocks list template
    """
    try:
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = get_current_user_settings().stocks_per_page
        offset = (page - 1) * per_page
        
        # Get stocks
        stocks = stock_service.get_stocks(limit=per_page, offset=offset)
        
        # Get portfolio summary
        portfolio_summary = stock_service.get_portfolio_summary()
        
        # Get recent stock transactions
        recent_transactions = stock_service.get_stock_transactions(limit=10)
        
        # Calculate pagination
        total_stocks = len(stock_service.get_stocks())
        total_pages = (total_stocks + per_page - 1) // per_page
        
        return render_template(
            'stocks/list.html',
            stocks=stocks,
            portfolio_summary=portfolio_summary,
            recent_transactions=recent_transactions,
            page=page,
            total_pages=total_pages,
            total_stocks=total_stocks,
            settings=get_current_user_settings()
        )
        
    except Exception as e:
        logger.error(f"Error listing stocks: {e}")
        flash_error("Unable to load stocks. Please try again.")
        return render_template(
            'stocks/list.html',
            stocks=[],
            portfolio_summary={},
            recent_transactions=[],
            settings=get_current_user_settings()
        )


@stocks_bp.route('/search')
def search_stocks():
    """
    Search for stocks using financial data API.
    
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
        
        stock_service = StockService(financial_data_service=get_financial_data_service())
        results = stock_service.search_stocks(query)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return jsonify({
            'success': False,
            'error': 'Stock search failed'
        }), 500


@stocks_bp.route('/add', methods=['GET', 'POST'])
def add_stock():
    """
    Add a new stock to tracking.
    
    Returns:
        GET: Rendered stock addition form
        POST: Redirect to stock detail or form with errors
    """
    if request.method == 'GET':
        return render_template(
            'stocks/add.html',
            settings=get_current_user_settings()
        )
    
    try:
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        # Get form data
        symbol = request.form.get('symbol', '').strip().upper()
        name = request.form.get('name', '').strip()
        
        # Validate required fields
        if not symbol:
            flash_error("Stock symbol is required.")
            return render_template(
                'stocks/add.html',
                settings=get_current_user_settings()
            )
        
        # Create stock (will fetch info from API if name not provided)
        stock = stock_service.create_stock(
            symbol=symbol,
            name=name or symbol,
            fetch_info=True
        )
        
        flash_success(f"Stock {stock.symbol} added successfully.")
        return redirect(url_for('stocks.view_stock', stock_id=stock.id))
        
    except Exception as e:
        logger.error(f"Error adding stock: {e}")
        flash_error("Failed to add stock. Please try again.")
        return render_template(
            'stocks/add.html',
            settings=get_current_user_settings()
        )


@stocks_bp.route('/view/stock_id=<int:stock_id>')
def view_stock(stock_id):
    """
    View stock details and holdings.
    
    Args:
        stock_id: Stock ID
        
    Returns:
        Rendered stock detail template
    """
    try:
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        # Get stock
        stock = stock_service.get_stock(stock_id)
        if not stock:
            flash_error("Stock not found.")
            return redirect(url_for('stocks.list_stocks'))
        
        # Get holdings for this stock
        holdings = stock_service.get_holdings(stock_id=stock_id)
        
        # Get stock transactions
        transactions = stock_service.get_stock_transactions(stock_id=stock_id, limit=20)
        
        # Get historical data for chart (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        historical_data = stock_service.get_stock_historical_data(
            stock.symbol, start_date, end_date
        )
        
        return render_template(
            'stocks/detail.html',
            stock=stock,
            holdings=holdings,
            transactions=transactions,
            historical_data=historical_data,
            settings=get_current_user_settings()
        )
        
    except Exception as e:
        logger.error(f"Error viewing stock {stock_id}: {e}")
        flash_error("Unable to load stock details.")
        return redirect(url_for('stocks.list_stocks'))


@stocks_bp.route('/<int:stock_id>/update-price', methods=['POST'])
def update_stock_price(stock_id):
    """
    Update stock price from financial data API.
    
    Args:
        stock_id: Stock ID
        
    Returns:
        JSON response with updated price
    """
    try:
        stock_service = StockService(financial_data_service=get_financial_data_service())
        
        stock = stock_service.update_stock_price(stock_id)
        if stock:
            return jsonify({
                'success': True,
                'price': float(stock.last_price) if stock.last_price else None,
                'formatted_price': stock.formatted_price,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Stock not found'
            }), 404
        
    except Exception as e:
        logger.error(f"Error updating stock price {stock_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update stock price'
        }), 500


@stocks_bp.route('/holdings/new', methods=['GET', 'POST'])
def create_holding():
    """
    Create a new stock holding.
    
    Returns:
        GET: Rendered holding creation form
        POST: Redirect to stocks list or form with errors
    """
    account_service = AccountService()
    stock_service = StockService()
    
    # Get brokerage accounts
    brokerage_accounts = account_service.get_accounts(
        account_type=AccountType.BROKERAGE,
        is_active=True
    )
    
    # Get all stocks
    stocks = stock_service.get_stocks()
    
    if request.method == 'GET':
        return render_template(
            'stocks/holding_form.html',
            holding=None,
            accounts=brokerage_accounts,
            stocks=stocks,
            settings=get_current_user_settings()
        )
    
    try:
        # Get form data
        account_id = request.form.get('account_id', type=int)
        stock_id = request.form.get('stock_id', type=int)
        shares_str = request.form.get('shares', '').strip()
        average_cost_str = request.form.get('average_cost', '').strip()
        purchase_date_str = request.form.get('purchase_date', '')
        notes = request.form.get('notes', '').strip() or None
        
        # Validate required fields
        errors = []
        
        if not account_id:
            errors.append("Account is required.")
        
        if not stock_id:
            errors.append("Stock is required.")
        
        if not shares_str:
            errors.append("Number of shares is required.")
        
        if not average_cost_str:
            errors.append("Average cost is required.")
        
        try:
            shares = Decimal(shares_str)
            if shares <= 0:
                errors.append("Number of shares must be positive.")
        except (ValueError, TypeError):
            errors.append("Invalid number of shares.")
            shares = None
        
        try:
            average_cost = Decimal(average_cost_str)
            if average_cost <= 0:
                errors.append("Average cost must be positive.")
        except (ValueError, TypeError):
            errors.append("Invalid average cost.")
            average_cost = None
        
        purchase_date = None
        if purchase_date_str:
            try:
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid purchase date format.")
        
        if errors:
            for error in errors:
                flash_error(error)
            return render_template(
                'stocks/holding_form.html',
                holding=None,
                accounts=brokerage_accounts,
                stocks=stocks,
                settings=get_current_user_settings()
            )
        
        # Create holding
        holding = stock_service.create_holding(
            account_id=account_id,
            stock_id=stock_id,
            shares=shares,
            average_cost=average_cost,
            purchase_date=purchase_date,
            notes=notes
        )
        
        flash_success("Stock holding created successfully.")
        return redirect(url_for('stocks.view_stock', stock_id=stock_id))
        
    except Exception as e:
        logger.error(f"Error creating holding: {e}")
        flash_error("Failed to create holding. Please try again.")
        return render_template(
            'stocks/holding_form.html',
            holding=None,
            accounts=brokerage_accounts,
            stocks=stocks,
            settings=get_current_user_settings()
        )


@stocks_bp.route('/transactions/new', methods=['GET', 'POST'])
def create_stock_transaction():
    """
    Create a new stock transaction (buy/sell).

    Returns:
        GET: Rendered stock transaction form
        POST: Redirect to stocks list or form with errors
    """
    account_service = AccountService()
    stock_service = StockService()

    # Get brokerage accounts
    brokerage_accounts = account_service.get_accounts(
        account_type=AccountType.BROKERAGE,
        is_active=True
    )

    # Get all stocks
    stocks = stock_service.get_stocks()

    if request.method == 'GET':
        return render_template(
            'stocks/transaction_form.html',
            transaction=None,
            accounts=brokerage_accounts,
            stocks=stocks,
            transaction_types=StockTransactionType,
            settings=get_current_user_settings()
        )

    try:
        # Get form data
        account_id = request.form.get('account_id', type=int)
        stock_id = request.form.get('stock_id', type=int)
        transaction_type_str = request.form.get('transaction_type', '')
        shares_str = request.form.get('shares', '').strip()
        price_per_share_str = request.form.get('price_per_share', '').strip()
        fees_str = request.form.get('fees', '0').strip()
        date_str = request.form.get('date', '')
        notes = request.form.get('notes', '').strip() or None

        # Validate required fields
        errors = []

        if not account_id:
            errors.append("Account is required.")

        if not stock_id:
            errors.append("Stock is required.")

        try:
            transaction_type = StockTransactionType(transaction_type_str)
        except ValueError:
            errors.append("Invalid transaction type.")
            transaction_type = None

        try:
            shares = Decimal(shares_str)
            if shares <= 0:
                errors.append("Number of shares must be positive.")
        except (ValueError, TypeError):
            errors.append("Invalid number of shares.")
            shares = None

        try:
            price_per_share = Decimal(price_per_share_str)
            if price_per_share <= 0:
                errors.append("Price per share must be positive.")
        except (ValueError, TypeError):
            errors.append("Invalid price per share.")
            price_per_share = None

        try:
            fees = Decimal(fees_str)
            if fees < 0:
                errors.append("Fees cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Invalid fees amount.")
            fees = Decimal('0')

        try:
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append("Invalid date format.")
            transaction_date = None

        if errors:
            for error in errors:
                flash_error(error)
            return render_template(
                'stocks/transaction_form.html',
                transaction=None,
                accounts=brokerage_accounts,
                stocks=stocks,
                transaction_types=StockTransactionType,
                settings=get_current_user_settings()
            )

        # Create stock transaction
        transaction = stock_service.create_stock_transaction(
            account_id=account_id,
            stock_id=stock_id,
            transaction_type=transaction_type,
            shares=shares,
            price_per_share=price_per_share,
            transaction_date=transaction_date,
            fees=fees,
            notes=notes,
            update_holding=True
        )

        flash_success(f"Stock transaction created successfully.")
        return redirect(url_for('stocks.view_stock', stock_id=stock_id))

    except Exception as e:
        logger.error(f"Error creating stock transaction: {e}")
        flash_error("Failed to create stock transaction. Please try again.")
        return render_template(
            'stocks/transaction_form.html',
            transaction=None,
            accounts=brokerage_accounts,
            stocks=stocks,
            transaction_types=StockTransactionType,
            settings=get_current_user_settings()
        )


@stocks_bp.route('/update-all-prices', methods=['POST'])
def update_all_prices():
    """
    Update prices for all stocks.

    Returns:
        JSON response with update results
    """
    try:
        stock_service = StockService(financial_data_service=get_financial_data_service())

        results = stock_service.update_all_stock_prices()

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        return jsonify({
            'success': True,
            'updated': success_count,
            'total': total_count,
            'results': results
        })

    except Exception as e:
        logger.error(f"Error updating all stock prices: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update stock prices'
        }), 500


@stocks_bp.route('/transactions')
def list_stock_transactions():
    """
    List all stock transactions.

    Returns:
        Rendered stock transactions list template
    """
    try:
        stock_service = StockService()

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = get_current_user_settings().transactions_per_page
        offset = (page - 1) * per_page

        # Get stock transactions
        transactions = stock_service.get_stock_transactions(limit=per_page, offset=offset)

        # Calculate pagination
        total_transactions = len(stock_service.get_stock_transactions())
        total_pages = (total_transactions + per_page - 1) // per_page

        return render_template(
            'stocks/transactions.html',
            transactions=transactions,
            page=page,
            total_pages=total_pages,
            total_transactions=total_transactions,
            settings=get_current_user_settings()
        )

    except Exception as e:
        logger.error(f"Error listing stock transactions: {e}")
        flash_error("Unable to load stock transactions. Please try again.")
        return render_template(
            'stocks/transactions.html',
            transactions=[],
            settings=get_current_user_settings()
        )


@stocks_bp.route('/lookup-info', methods=['POST'])
def lookup_stock_info():
    """
    Lookup stock information from financial data API.

    Returns:
        JSON response with stock information
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()

        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Stock symbol is required'
            }), 400

        stock_service = StockService(financial_data_service=get_financial_data_service())
        stock_info = stock_service.financial_data_service.get_stock_info(symbol)

        if stock_info:
            return jsonify({
                'success': True,
                'stock_info': stock_info
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Could not find information for symbol {symbol}'
            })

    except Exception as e:
        logger.error(f"Error looking up stock info: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to lookup stock information'
        }), 500


@stocks_bp.route('/transactions/<int:transaction_id>/delete', methods=['POST'])
def delete_stock_transaction(transaction_id):
    """
    Delete a stock transaction.

    Args:
        transaction_id: Stock transaction ID

    Returns:
        Redirect to stocks list
    """
    try:
        stock_service = StockService()

        if stock_service.delete_stock_transaction(transaction_id):
            flash_success("Stock transaction deleted successfully.")
        else:
            flash_error("Stock transaction not found.")

    except Exception as e:
        logger.error(f"Error deleting stock transaction {transaction_id}: {e}")
        flash_error("Failed to delete stock transaction. Please try again.")

    return redirect(url_for('stocks.list_stocks'))
