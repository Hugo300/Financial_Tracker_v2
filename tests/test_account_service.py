"""
Unit tests for the Account Service.

This module tests the AccountService class functionality including
CRUD operations, balance management, and account analytics.
"""

import pytest
from decimal import Decimal
from datetime import date

from src.models import AccountType
from src.services import AccountService


class TestAccountService:
    """Test cases for AccountService."""
    
    def test_create_account(self, db_session):
        """Test creating a new account."""
        service = AccountService(db_session)
        
        account = service.create_account(
            name="Test Account",
            account_type=AccountType.CHECKING,
            balance=Decimal('1000.00'),
            currency='$',
            description="Test account",
            institution="Test Bank",
            account_number="1234567890",
            is_active=True
        )
        
        assert account.id is not None
        assert account.name == "Test Account"
        assert account.account_type == AccountType.CHECKING
        assert account.balance == Decimal('1000.00')
        assert account.currency == '$'
        assert account.description == "Test account"
        assert account.institution == "Test Bank"
        assert account.account_number == "1234567890"
        assert account.is_active is True
        assert account.created_at is not None
        assert account.updated_at is not None
    
    def test_create_account_minimal(self, db_session):
        """Test creating an account with minimal required fields."""
        service = AccountService(db_session)
        
        account = service.create_account(
            name="Minimal Account",
            account_type=AccountType.SAVINGS
        )
        
        assert account.id is not None
        assert account.name == "Minimal Account"
        assert account.account_type == AccountType.SAVINGS
        assert account.balance == Decimal('0.00')
        assert account.currency == '$'
        assert account.description is None
        assert account.institution is None
        assert account.account_number is None
        assert account.is_active is True
    
    def test_get_account(self, db_session, sample_account):
        """Test retrieving an account by ID."""
        service = AccountService(db_session)
        
        retrieved_account = service.get_account(sample_account.id)
        
        assert retrieved_account is not None
        assert retrieved_account.id == sample_account.id
        assert retrieved_account.name == sample_account.name
        assert retrieved_account.account_type == sample_account.account_type
    
    def test_get_account_not_found(self, db_session):
        """Test retrieving a non-existent account."""
        service = AccountService(db_session)
        
        account = service.get_account(99999)
        
        assert account is None
    
    def test_get_accounts_all(self, db_session, multiple_accounts):
        """Test retrieving all accounts."""
        service = AccountService(db_session)
        
        accounts = service.get_accounts()
        
        assert len(accounts) == 5  # All accounts including inactive
        assert all(account.name for account in accounts)
    
    def test_get_accounts_by_type(self, db_session, multiple_accounts):
        """Test filtering accounts by type."""
        service = AccountService(db_session)
        
        checking_accounts = service.get_accounts(account_type=AccountType.CHECKING)
        
        assert len(checking_accounts) == 2  # Two checking accounts
        assert all(account.account_type == AccountType.CHECKING for account in checking_accounts)
    
    def test_get_accounts_active_only(self, db_session, multiple_accounts):
        """Test filtering accounts by active status."""
        service = AccountService(db_session)
        
        active_accounts = service.get_accounts(is_active=True)
        
        assert len(active_accounts) == 4  # Four active accounts
        assert all(account.is_active for account in active_accounts)
    
    def test_get_accounts_by_institution(self, db_session):
        """Test filtering accounts by institution."""
        service = AccountService(db_session)
        
        # Create accounts with specific institution
        service.create_account(
            name="Bank A Account 1",
            account_type=AccountType.CHECKING,
            institution="Bank A"
        )
        service.create_account(
            name="Bank A Account 2",
            account_type=AccountType.SAVINGS,
            institution="Bank A"
        )
        service.create_account(
            name="Bank B Account",
            account_type=AccountType.CHECKING,
            institution="Bank B"
        )
        
        bank_a_accounts = service.get_accounts(institution="Bank A")
        
        assert len(bank_a_accounts) == 2
        assert all(account.institution == "Bank A" for account in bank_a_accounts)
    
    def test_update_account(self, db_session, sample_account):
        """Test updating account information."""
        service = AccountService(db_session)
        
        updated_account = service.update_account(
            account_id=sample_account.id,
            name="Updated Account Name",
            description="Updated description",
            institution="Updated Bank",
            is_active=False
        )
        
        assert updated_account is not None
        assert updated_account.name == "Updated Account Name"
        assert updated_account.description == "Updated description"
        assert updated_account.institution == "Updated Bank"
        assert updated_account.is_active is False
        assert updated_account.updated_at > updated_account.created_at
    
    def test_update_account_not_found(self, db_session):
        """Test updating a non-existent account."""
        service = AccountService(db_session)
        
        result = service.update_account(
            account_id=99999,
            name="Non-existent Account"
        )
        
        assert result is None
    
    def test_delete_account_without_transactions(self, db_session, sample_account):
        """Test deleting an account with no transactions (hard delete)."""
        service = AccountService(db_session)
        account_id = sample_account.id
        
        result = service.delete_account(account_id)
        
        assert result is True
        
        # Verify account is actually deleted
        deleted_account = service.get_account(account_id)
        assert deleted_account is None
    
    def test_delete_account_with_transactions(self, db_session, sample_account, sample_transaction):
        """Test deleting an account with transactions (soft delete)."""
        service = AccountService(db_session)
        account_id = sample_account.id
        
        result = service.delete_account(account_id)
        
        assert result is True
        
        # Verify account is deactivated, not deleted
        deactivated_account = service.get_account(account_id)
        assert deactivated_account is not None
        assert deactivated_account.is_active is False
    
    def test_delete_account_not_found(self, db_session):
        """Test deleting a non-existent account."""
        service = AccountService(db_session)
        
        result = service.delete_account(99999)
        
        assert result is False
    
    def test_update_balance(self, db_session, sample_account):
        """Test updating account balance."""
        service = AccountService(db_session)
        initial_balance = sample_account.balance
        
        updated_account = service.update_balance(sample_account.id, Decimal('250.00'))
        
        assert updated_account is not None
        assert updated_account.balance == initial_balance + Decimal('250.00')
        assert updated_account.updated_at > updated_account.created_at
    
    def test_update_balance_negative(self, db_session, sample_account):
        """Test updating account balance with negative amount."""
        service = AccountService(db_session)
        initial_balance = sample_account.balance
        
        updated_account = service.update_balance(sample_account.id, Decimal('-100.00'))
        
        assert updated_account is not None
        assert updated_account.balance == initial_balance - Decimal('100.00')
    
    def test_update_balance_not_found(self, db_session):
        """Test updating balance for non-existent account."""
        service = AccountService(db_session)
        
        result = service.update_balance(99999, Decimal('100.00'))
        
        assert result is None
    
    def test_get_account_summary(self, db_session, multiple_accounts):
        """Test getting account summary statistics."""
        service = AccountService(db_session)
        
        summary = service.get_account_summary()
        
        assert 'total_assets' in summary
        assert 'total_liabilities' in summary
        assert 'net_worth' in summary
        assert 'account_counts' in summary
        assert 'balances_by_type' in summary
        assert 'total_accounts' in summary
        
        # Check calculations
        expected_assets = Decimal('42500.00')  # 2500 + 15000 + 25000
        expected_liabilities = Decimal('1200.00')  # abs(-1200)
        expected_net_worth = expected_assets - expected_liabilities
        
        assert summary['total_assets'] == expected_assets
        assert summary['total_liabilities'] == expected_liabilities
        assert summary['net_worth'] == expected_net_worth
        assert summary['total_accounts'] == 4  # Only active accounts
    
    def test_get_balance_history(self, db_session, sample_account):
        """Test getting balance history for an account."""
        from src.services import TransactionService
        from src.models import TransactionType, TransactionCategory

        account_service = AccountService(db_session)
        transaction_service = TransactionService(db_session)

        # Create some transactions for the account
        transactions_data = [
            (Decimal('1000.00'), TransactionType.INCOME, "Salary"),
            (Decimal('-200.00'), TransactionType.EXPENSE, "Groceries"),
            (Decimal('-50.00'), TransactionType.EXPENSE, "Gas")
        ]

        for amount, t_type, description in transactions_data:
            transaction_service.create_transaction(
                account_id=sample_account.id,
                amount=amount,
                transaction_type=t_type,
                description=description,
                transaction_date=date.today(),
                update_balance=False  # Don't update balance to keep test simple
            )

        history = account_service.get_balance_history(sample_account.id, days=30)

        assert isinstance(history, list)
        assert len(history) > 0

        # Check that history entries have required fields
        for entry in history:
            assert 'date' in entry
            assert 'balance' in entry
            assert 'transaction_amount' in entry or entry['transaction_amount'] is None
            assert 'description' in entry
    
    def test_get_balance_history_no_transactions(self, db_session, sample_account):
        """Test getting balance history for account with no transactions."""
        service = AccountService(db_session)
        
        history = service.get_balance_history(sample_account.id, days=30)
        
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_get_balance_history_not_found(self, db_session):
        """Test getting balance history for non-existent account."""
        service = AccountService(db_session)
        
        history = service.get_balance_history(99999, days=30)
        
        assert isinstance(history, list)
        assert len(history) == 0
