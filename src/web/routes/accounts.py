"""
Account routes for the Financial Tracker application.

This module handles account management including CRUD operations
and account-specific views.
"""

import logging
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response

from ...models import AccountType
from ...services import AccountService, TransactionService, StockService
from ..app import get_current_user_settings, flash_success, flash_error

logger = logging.getLogger(__name__)

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/')
def list_accounts():
    """
    List all accounts with summary information.
    
    Returns:
        Rendered accounts list template
    """
    try:
        account_service = AccountService()
        stock_service = StockService()
        
        # Get filter parameters
        account_type = request.args.get('type')
        is_active = request.args.get('active')
        
        # Convert string parameters to appropriate types
        type_filter = None
        if account_type:
            try:
                type_filter = AccountType(account_type)
            except ValueError:
                pass
        
        active_filter = None
        if is_active is not None:
            active_filter = is_active.lower() == 'true'
        
        # Get accounts
        accounts = account_service.get_accounts(
            account_type=type_filter,
            is_active=active_filter
        )

        for account in accounts:
            if account.account_type == AccountType.BROKERAGE:
                stock_value = stock_service.get_portfolio_summary(account_id=account.id)['total_value']
                account.balance = account.balance + stock_value
        
        # Get account summary
        summary = account_service.get_account_summary()
        
        return render_template(
            'accounts/list.html',
            accounts=accounts,
            summary=summary,
            account_types=AccountType,
            current_type=account_type,
            current_active=is_active,
            settings=get_current_user_settings()
        )
        
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        flash_error("Unable to load accounts. Please try again.")
        return render_template(
            'accounts/list.html',
            accounts=[],
            summary={},
            account_types=AccountType,
            settings=get_current_user_settings()
        )


@accounts_bp.route('/new', methods=['GET', 'POST'])
def create_account():
    """
    Create a new account.
    
    Returns:
        GET: Rendered account creation form
        POST: Redirect to account list or form with errors
    """
    if request.method == 'GET':
        return render_template(
            'accounts/form.html',
            account=None,
            account_types=AccountType,
            settings=get_current_user_settings()
        )
    
    try:
        account_service = AccountService()
        
        # Get form data
        name = request.form.get('name', '').strip()
        account_type_str = request.form.get('account_type', '')
        balance_str = request.form.get('balance', '0')
        currency = request.form.get('currency', '$').strip()
        description = request.form.get('description', '').strip() or None
        institution = request.form.get('institution', '').strip() or None
        account_number = request.form.get('account_number', '').strip() or None
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not name:
            flash_error("Account name is required.")
            return render_template(
                'accounts/form.html',
                account=None,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
        try:
            account_type = AccountType(account_type_str)
        except ValueError:
            flash_error("Invalid account type.")
            return render_template(
                'accounts/form.html',
                account=None,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
        try:
            balance = Decimal(balance_str)
        except (ValueError, TypeError):
            flash_error("Invalid balance amount.")
            return render_template(
                'accounts/form.html',
                account=None,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
        # Create account
        account = account_service.create_account(
            name=name,
            account_type=account_type,
            balance=balance,
            currency=currency,
            description=description,
            institution=institution,
            account_number=account_number,
            is_active=is_active
        )
        
        flash_success(f"Account '{account.name}' created successfully.")
        return redirect(url_for('accounts.view_account', account_id=account.id))
        
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        flash_error("Failed to create account. Please try again.")
        return render_template(
            'accounts/form.html',
            account=None,
            account_types=AccountType,
            settings=get_current_user_settings()
        )


@accounts_bp.route('/<int:account_id>')
def view_account(account_id):
    """
    View account details and recent transactions.
    
    Args:
        account_id: Account ID
        
    Returns:
        Rendered account detail template
    """
    try:
        account_service = AccountService()
        transaction_service = TransactionService()
        stock_service = StockService()
        
        # Get account
        account = account_service.get_account(account_id)
        if not account:
            flash_error("Account not found.")
            return redirect(url_for('accounts.list_accounts'))
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = get_current_user_settings().transactions_per_page
        offset = (page - 1) * per_page
        
        # Get transactions for this account
        transactions = transaction_service.get_transactions(
            account_id=account_id,
            limit=per_page,
            offset=offset
        )
        
        # Get total transaction count for pagination
        total_transactions = account.get_transaction_count()
        total_pages = (total_transactions + per_page - 1) // per_page
        
        # Get balance history
        balance_history = account_service.get_balance_history(account_id, days=30)
        
        # if its a brokerage account, get the total value of stocks
        if account.account_type == AccountType.BROKERAGE:
            stock_service = StockService()
            stock_value = stock_service.get_portfolio_summary(account_id=account.id)['total_value']
            cash_value = account.balance
        else:
            stock_value = Decimal('0.00')
            cash_value = account.balance

        print(account)
        print({'cash_value': cash_value, 'stock_value': stock_value})
        return render_template(
            'accounts/detail.html',
            account=account,
            values={'cash_value': cash_value, 'stock_value': stock_value, 'total_value': cash_value + stock_value},
            transactions=transactions,
            balance_history=balance_history,
            page=page,
            total_pages=total_pages,
            total_transactions=total_transactions,
            settings=get_current_user_settings()
        )
        
    except Exception as e:
        logger.error(f"Error viewing account {account_id}: {e}")
        flash_error("Unable to load account details.")
        return redirect(url_for('accounts.list_accounts'))


@accounts_bp.route('/<int:account_id>/export')
def export_transactions(account_id):
    """
    Export transactions for a specific account to CSV.

    Args:
        account_id: Account ID

    Returns:
        CSV file download
    """
    try:
        account_service = AccountService()
        transaction_service = TransactionService()

        # Get account
        account = account_service.get_account(account_id)
        if not account:
            flash_error("Account not found.")
            return redirect(url_for('accounts.list_accounts'))

        # Get all transactions for this account
        transactions = transaction_service.get_transactions(account_id=account_id)

        # Export to CSV
        csv_content = transaction_service.export_to_csv(transactions)

        # Create response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={account.name}_transactions.csv'

        return response

    except Exception as e:
        logger.error(f"Error exporting transactions for account {account_id}: {e}")
        flash_error("Failed to export transactions. Please try again.")
        return redirect(url_for('accounts.view_account', account_id=account_id))


@accounts_bp.route('/<int:account_id>/edit', methods=['GET', 'POST'])
def edit_account(account_id):
    """
    Edit an existing account.
    
    Args:
        account_id: Account ID
        
    Returns:
        GET: Rendered account edit form
        POST: Redirect to account detail or form with errors
    """
    try:
        account_service = AccountService()
        account = account_service.get_account(account_id)
        
        if not account:
            flash_error("Account not found.")
            return redirect(url_for('accounts.list_accounts'))
        
        if request.method == 'GET':
            return render_template(
                'accounts/form.html',
                account=account,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
        # Handle POST request
        name = request.form.get('name', '').strip()
        balance = request.form.get('balance', '0').strip()
        currency = request.form.get('currency', '$').strip()
        description = request.form.get('description', '').strip() or None
        institution = request.form.get('institution', '').strip() or None
        account_number = request.form.get('account_number', '').strip() or None
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not name:
            flash_error("Account name is required.")
            return render_template(
                'accounts/form.html',
                account=account,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
        try:
            balance = Decimal(balance)
        except (ValueError, TypeError):
            flash_error("Invalid balance amount.")
            return render_template(
                'accounts/form.html',
                account=account,
                account_types=AccountType,
                settings=get_current_user_settings()
            )

        # Update account
        updated_account = account_service.update_account(
            account_id=account_id,
            name=name,
            balance=balance,
            currency=currency,
            description=description,
            institution=institution,
            account_number=account_number,
            is_active=is_active
        )
        
        if updated_account:
            flash_success(f"Account '{updated_account.name}' updated successfully.")
            return redirect(url_for('accounts.view_account', account_id=account_id))
        else:
            flash_error("Failed to update account.")
            return render_template(
                'accounts/form.html',
                account=account,
                account_types=AccountType,
                settings=get_current_user_settings()
            )
        
    except Exception as e:
        logger.error(f"Error editing account {account_id}: {e}")
        flash_error("Failed to update account. Please try again.")
        return redirect(url_for('accounts.view_account', account_id=account_id))


@accounts_bp.route('/<int:account_id>/delete', methods=['POST'])
def delete_account(account_id):
    """
    Delete an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Redirect to accounts list
    """
    try:
        account_service = AccountService()
        
        if account_service.delete_account(account_id):
            flash_success("Account deleted successfully.")
        else:
            flash_error("Account not found.")
        
    except Exception as e:
        logger.error(f"Error deleting account {account_id}: {e}")
        flash_error("Failed to delete account. Please try again.")
    
    return redirect(url_for('accounts.list_accounts'))
