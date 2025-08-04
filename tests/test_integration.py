"""
Integration tests for the Financial Tracker application.

This module tests the integration between different components
including database operations and API interactions.
"""

import pytest
from decimal import Decimal
from datetime import date
import json

from src.models import AccountType, TransactionType, TransactionCategory, StockTransactionType


class TestDatabaseIntegration:
    """Test database operations and model relationships."""
    
    def test_account_transaction_relationship(self, db_session, sample_account):
        """Test the relationship between accounts and transactions."""
        from src.services import TransactionService
        
        service = TransactionService(db_session)
        
        # Create transactions for the account
        transactions_data = [
            (Decimal('1000.00'), TransactionType.INCOME, "Salary"),
            (Decimal('-200.00'), TransactionType.EXPENSE, "Groceries"),
            (Decimal('-50.00'), TransactionType.EXPENSE, "Gas")
        ]
        
        created_transactions = []
        for amount, t_type, description in transactions_data:
            transaction = service.create_transaction(
                account_id=sample_account.id,
                amount=amount,
                transaction_type=t_type,
                description=description,
                transaction_date=date.today(),
                update_balance=True
            )
            created_transactions.append(transaction)
        
        # Refresh account to get updated data
        db_session.refresh(sample_account)
        
        # Test account balance was updated correctly
        expected_balance = Decimal('1000.00') + Decimal('1000.00') - Decimal('200.00') - Decimal('50.00')
        assert sample_account.balance == expected_balance
        
        # Test transaction count
        assert sample_account.get_transaction_count() == 3
        
        # Test recent transactions
        recent = sample_account.get_recent_transactions(limit=2)
        assert len(recent) == 2
        
        # Test relationship access
        for transaction in created_transactions:
            assert transaction.account.id == sample_account.id
            assert transaction.account.name == sample_account.name
    
    def test_stock_holding_relationship(self, db_session, sample_brokerage_account, sample_stock):
        """Test the relationship between stocks, holdings, and accounts."""
        from src.services import StockService
        
        service = StockService(db_session)
        
        # Create holding
        holding = service.create_holding(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            shares=Decimal('15.0'),
            average_cost=Decimal('145.00'),
            purchase_date=date.today()
        )
        
        # Test relationships
        assert holding.account.id == sample_brokerage_account.id
        assert holding.stock.id == sample_stock.id
        assert holding.stock.symbol == sample_stock.symbol
        
        # Test stock total shares calculation
        total_shares = sample_stock.get_total_shares()
        assert total_shares == Decimal('15.0')
        
        # Test stock total value calculation
        total_value = sample_stock.get_total_value()
        expected_value = Decimal('15.0') * sample_stock.last_price
        assert total_value == expected_value
    
    def test_stock_transaction_holding_integration(self, db_session, sample_brokerage_account, sample_stock):
        """Test integration between stock transactions and holdings."""
        from src.services import StockService
        
        service = StockService(db_session)
        
        # Create initial buy transaction
        buy_transaction = service.create_stock_transaction(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=Decimal('10.0'),
            price_per_share=Decimal('140.00'),
            transaction_date=date.today(),
            update_holding=True
        )
        
        # Check holding was created
        holdings = service.get_holdings(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id
        )
        assert len(holdings) == 1
        holding = holdings[0]
        assert holding.shares == Decimal('10.0')
        assert holding.average_cost == Decimal('140.00')
        
        # Create another buy transaction
        service.create_stock_transaction(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=Decimal('5.0'),
            price_per_share=Decimal('160.00'),
            transaction_date=date.today(),
            update_holding=True
        )
        
        # Check holding was updated correctly
        db_session.refresh(holding)
        assert holding.shares == Decimal('15.0')
        # Average cost should be weighted: (10*140 + 5*160) / 15 = 146.67
        expected_avg_cost = (Decimal('10.0') * Decimal('140.00') + Decimal('5.0') * Decimal('160.00')) / Decimal('15.0')
        assert abs(holding.average_cost - expected_avg_cost) < Decimal('0.01')
        
        # Create sell transaction
        service.create_stock_transaction(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            transaction_type=StockTransactionType.SELL,
            shares=Decimal('3.0'),
            price_per_share=Decimal('155.00'),
            transaction_date=date.today(),
            update_holding=True
        )
        
        # Check holding was reduced
        db_session.refresh(holding)
        assert holding.shares == Decimal('12.0')


class TestWebIntegration:
    """Test web application integration."""
    
    def test_dashboard_loads(self, client):
        """Test that the dashboard loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        assert b'Net Worth' in response.data
    
    def test_accounts_list_loads(self, client):
        """Test that the accounts list loads successfully."""
        response = client.get('/accounts/')
        assert response.status_code == 200
        assert b'Accounts' in response.data
    
    def test_create_account_flow(self, client):
        """Test the complete account creation flow."""
        # Get the form
        response = client.get('/accounts/new')
        assert response.status_code == 200
        assert b'Add Account' in response.data or b'Create Account' in response.data
        
        # Submit the form
        response = client.post('/accounts/new', data={
            'name': 'Test Integration Account',
            'account_type': 'checking',
            'balance': '1500.00',
            'currency': '$',
            'description': 'Integration test account',
            'institution': 'Test Bank',
            'account_number': '123456789',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to account detail or list
        assert b'Test Integration Account' in response.data
    
    def test_transactions_list_loads(self, client):
        """Test that the transactions list loads successfully."""
        response = client.get('/transactions/')
        assert response.status_code == 200
        assert b'Transactions' in response.data
    
    def test_stocks_list_loads(self, client):
        """Test that the stocks list loads successfully."""
        response = client.get('/stocks/')
        assert response.status_code == 200
        assert b'Stocks' in response.data or b'Portfolio' in response.data
    
    def test_settings_loads(self, client):
        """Test that the settings page loads successfully."""
        response = client.get('/settings/')
        assert response.status_code == 200
        assert b'Settings' in response.data
    
    def test_api_dashboard_refresh(self, client):
        """Test the dashboard refresh API endpoint."""
        response = client.get('/api/dashboard/refresh')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'data' in data
        
        if data['success']:
            assert 'net_worth' in data['data']
            assert 'total_assets' in data['data']
            assert 'total_liabilities' in data['data']
    
    def test_search_api(self, client):
        """Test the search API endpoint."""
        response = client.get('/search?q=test')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'results' in data
        assert isinstance(data['results'], list)
    
    def test_404_error_page(self, client):
        """Test that 404 errors are handled properly."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'404' in response.data or b'Not Found' in response.data


class TestServiceIntegration:
    """Test integration between different services."""
    
    def test_account_transaction_service_integration(self, db_session):
        """Test integration between AccountService and TransactionService."""
        from src.services import AccountService, TransactionService
        
        account_service = AccountService(db_session)
        transaction_service = TransactionService(db_session)
        
        # Create account
        account = account_service.create_account(
            name="Integration Test Account",
            account_type=AccountType.CHECKING,
            balance=Decimal('1000.00')
        )
        
        # Create transactions
        transaction1 = transaction_service.create_transaction(
            account_id=account.id,
            amount=Decimal('500.00'),
            transaction_type=TransactionType.INCOME,
            description="Income transaction",
            transaction_date=date.today(),
            update_balance=True
        )
        
        transaction2 = transaction_service.create_transaction(
            account_id=account.id,
            amount=Decimal('-200.00'),
            transaction_type=TransactionType.EXPENSE,
            description="Expense transaction",
            transaction_date=date.today(),
            update_balance=True
        )
        
        # Verify account balance was updated
        updated_account = account_service.get_account(account.id)
        expected_balance = Decimal('1000.00') + Decimal('500.00') - Decimal('200.00')
        assert updated_account.balance == expected_balance
        
        # Verify transactions are linked to account
        account_transactions = transaction_service.get_transactions(account_id=account.id)
        assert len(account_transactions) == 2
        
        # Test transaction summary for account
        summary = transaction_service.get_transaction_summary(account_id=account.id)
        assert summary['total_income'] == Decimal('500.00')
        assert summary['total_expenses'] == Decimal('200.00')
        assert summary['net_income'] == Decimal('300.00')
    
    def test_stock_service_integration(self, db_session):
        """Test integration of stock-related services."""
        from src.services import StockService, AccountService
        
        account_service = AccountService(db_session)
        stock_service = StockService(db_session)
        
        # Create brokerage account
        brokerage_account = account_service.create_account(
            name="Integration Brokerage",
            account_type=AccountType.BROKERAGE,
            balance=Decimal('10000.00')
        )
        
        # Create stock
        stock = stock_service.create_stock(
            symbol="INTG",
            name="Integration Test Corp",
            fetch_info=False
        )
        
        # Update stock price
        stock.last_price = Decimal('100.00')
        db_session.commit()
        
        # Create stock transaction and holding
        stock_transaction = stock_service.create_stock_transaction(
            account_id=brokerage_account.id,
            stock_id=stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=Decimal('50.0'),
            price_per_share=Decimal('95.00'),
            transaction_date=date.today(),
            update_holding=True
        )
        
        # Verify holding was created
        holdings = stock_service.get_holdings(account_id=brokerage_account.id)
        assert len(holdings) == 1
        holding = holdings[0]
        assert holding.shares == Decimal('50.0')
        assert holding.average_cost == Decimal('95.00')
        
        # Test portfolio summary
        portfolio_summary = stock_service.get_portfolio_summary(account_id=brokerage_account.id)
        assert portfolio_summary['holdings_count'] == 1
        assert portfolio_summary['total_cost'] == Decimal('4750.00')  # 50 * 95
        assert portfolio_summary['total_value'] == Decimal('5000.00')  # 50 * 100
        assert portfolio_summary['total_gain_loss'] == Decimal('250.00')  # 5000 - 4750
        
        # Test stock transactions
        transactions = stock_service.get_stock_transactions(account_id=brokerage_account.id)
        assert len(transactions) == 1
        assert transactions[0].id == stock_transaction.id
