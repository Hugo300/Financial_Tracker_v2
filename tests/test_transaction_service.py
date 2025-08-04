"""
Unit tests for the Transaction Service.

This module tests the TransactionService class functionality including
CRUD operations, CSV import/export, and transaction analytics.
"""

import pytest
from decimal import Decimal
from datetime import date
import io

from src.models import TransactionType, TransactionCategory
from src.services import TransactionService


class TestTransactionService:
    """Test cases for TransactionService."""
    
    def test_create_transaction(self, db_session, sample_account):
        """Test creating a new transaction."""
        service = TransactionService(db_session)
        
        transaction = service.create_transaction(
            account_id=sample_account.id,
            amount=Decimal('-75.50'),
            transaction_type=TransactionType.EXPENSE,
            description="Test expense",
            transaction_date=date.today(),
            category=TransactionCategory.FOOD,
            payee="Test Store",
            reference="REF123",
            tags="test, food",
            notes="Test transaction",
            update_balance=False  # Don't update balance for this test
        )
        
        assert transaction.id is not None
        assert transaction.account_id == sample_account.id
        assert transaction.amount == Decimal('-75.50')
        assert transaction.transaction_type == TransactionType.EXPENSE
        assert transaction.description == "Test expense"
        assert transaction.date == date.today()
        assert transaction.category == TransactionCategory.FOOD
        assert transaction.payee == "Test Store"
        assert transaction.reference == "REF123"
        assert transaction.tags == "test, food"
        assert transaction.notes == "Test transaction"
    
    def test_create_transaction_with_balance_update(self, db_session, sample_account):
        """Test creating a transaction that updates account balance."""
        service = TransactionService(db_session)
        initial_balance = sample_account.balance
        
        transaction = service.create_transaction(
            account_id=sample_account.id,
            amount=Decimal('-100.00'),
            transaction_type=TransactionType.EXPENSE,
            description="Balance update test",
            transaction_date=date.today(),
            update_balance=True
        )
        
        assert transaction.id is not None
        
        # Refresh account to get updated balance
        db_session.refresh(sample_account)
        assert sample_account.balance == initial_balance - Decimal('100.00')
    
    def test_get_transaction(self, db_session, sample_transaction):
        """Test retrieving a transaction by ID."""
        service = TransactionService(db_session)
        
        retrieved_transaction = service.get_transaction(sample_transaction.id)
        
        assert retrieved_transaction is not None
        assert retrieved_transaction.id == sample_transaction.id
        assert retrieved_transaction.description == sample_transaction.description
        assert retrieved_transaction.amount == sample_transaction.amount
    
    def test_get_transaction_not_found(self, db_session):
        """Test retrieving a non-existent transaction."""
        service = TransactionService(db_session)
        
        transaction = service.get_transaction(99999)
        
        assert transaction is None
    
    def test_get_transactions_all(self, db_session, multiple_transactions):
        """Test retrieving all transactions."""
        service = TransactionService(db_session)
        
        transactions = service.get_transactions()
        
        assert len(transactions) == 4
        # Should be ordered by date desc, then created_at desc
        assert transactions[0].date >= transactions[1].date
    
    def test_get_transactions_by_account(self, db_session, sample_account, multiple_transactions):
        """Test filtering transactions by account."""
        service = TransactionService(db_session)
        
        transactions = service.get_transactions(account_id=sample_account.id)
        
        assert len(transactions) == 4
        assert all(t.account_id == sample_account.id for t in transactions)
    
    def test_get_transactions_by_type(self, db_session, multiple_transactions):
        """Test filtering transactions by type."""
        service = TransactionService(db_session)
        
        expense_transactions = service.get_transactions(transaction_type=TransactionType.EXPENSE)
        
        assert len(expense_transactions) == 3
        assert all(t.transaction_type == TransactionType.EXPENSE for t in expense_transactions)
    
    def test_get_transactions_by_category(self, db_session, multiple_transactions):
        """Test filtering transactions by category."""
        service = TransactionService(db_session)
        
        food_transactions = service.get_transactions(category=TransactionCategory.FOOD)
        
        assert len(food_transactions) == 1
        assert all(t.category == TransactionCategory.FOOD for t in food_transactions)
    
    def test_get_transactions_by_date_range(self, db_session, multiple_transactions):
        """Test filtering transactions by date range."""
        service = TransactionService(db_session)
        
        transactions = service.get_transactions(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2)
        )
        
        assert len(transactions) == 3  # Transactions on Jan 1 and Jan 2
        assert all(date(2024, 1, 1) <= t.date <= date(2024, 1, 2) for t in transactions)
    
    def test_get_transactions_with_pagination(self, db_session, multiple_transactions):
        """Test transaction pagination."""
        service = TransactionService(db_session)
        
        # Get first 2 transactions
        page1 = service.get_transactions(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get next 2 transactions
        page2 = service.get_transactions(limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure no overlap
        page1_ids = {t.id for t in page1}
        page2_ids = {t.id for t in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_update_transaction(self, db_session, sample_transaction):
        """Test updating transaction information."""
        service = TransactionService(db_session)
        
        updated_transaction = service.update_transaction(
            transaction_id=sample_transaction.id,
            description="Updated description",
            amount=Decimal('-60.00'),
            category=TransactionCategory.ENTERTAINMENT,
            payee="Updated Store",
            update_balance=False
        )
        
        assert updated_transaction is not None
        assert updated_transaction.description == "Updated description"
        assert updated_transaction.amount == Decimal('-60.00')
        assert updated_transaction.category == TransactionCategory.ENTERTAINMENT
        assert updated_transaction.payee == "Updated Store"
        assert updated_transaction.updated_at > updated_transaction.created_at
    
    def test_update_transaction_not_found(self, db_session):
        """Test updating a non-existent transaction."""
        service = TransactionService(db_session)
        
        result = service.update_transaction(
            transaction_id=99999,
            description="Non-existent transaction"
        )
        
        assert result is None
    
    def test_delete_transaction(self, db_session, sample_transaction):
        """Test deleting a transaction."""
        service = TransactionService(db_session)
        transaction_id = sample_transaction.id
        
        result = service.delete_transaction(transaction_id, update_balance=False)
        
        assert result is True
        
        # Verify transaction is deleted
        deleted_transaction = service.get_transaction(transaction_id)
        assert deleted_transaction is None
    
    def test_delete_transaction_with_balance_update(self, db_session, sample_account):
        """Test deleting a transaction with balance update."""
        service = TransactionService(db_session)
        initial_balance = sample_account.balance
        
        # Create transaction
        transaction = service.create_transaction(
            account_id=sample_account.id,
            amount=Decimal('-50.00'),
            transaction_type=TransactionType.EXPENSE,
            description="To be deleted",
            transaction_date=date.today(),
            update_balance=True
        )
        
        # Verify balance was updated
        db_session.refresh(sample_account)
        assert sample_account.balance == initial_balance - Decimal('50.00')
        
        # Delete transaction with balance update
        result = service.delete_transaction(transaction.id, update_balance=True)
        assert result is True
        
        # Verify balance was restored
        db_session.refresh(sample_account)
        assert sample_account.balance == initial_balance
    
    def test_delete_transaction_not_found(self, db_session):
        """Test deleting a non-existent transaction."""
        service = TransactionService(db_session)
        
        result = service.delete_transaction(99999)
        
        assert result is False
    
    def test_get_transaction_summary(self, db_session, multiple_transactions):
        """Test getting transaction summary statistics."""
        service = TransactionService(db_session)
        
        summary = service.get_transaction_summary()
        
        assert 'total_income' in summary
        assert 'total_expenses' in summary
        assert 'net_income' in summary
        assert 'transaction_counts' in summary
        assert 'category_spending' in summary
        assert 'total_transactions' in summary
        
        # Check calculations based on multiple_transactions fixture
        assert summary['total_income'] == Decimal('2000.00')
        assert summary['total_expenses'] == Decimal('650.00')  # 500 + 100 + 50
        assert summary['net_income'] == Decimal('1350.00')  # 2000 - 650
        assert summary['total_transactions'] == 4
    
    def test_get_transaction_summary_with_filters(self, db_session, sample_account, multiple_transactions):
        """Test getting transaction summary with filters."""
        service = TransactionService(db_session)
        
        summary = service.get_transaction_summary(
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 3),
            account_id=sample_account.id
        )
        
        # Should only include transactions from Jan 2-3
        assert summary['total_expenses'] == Decimal('150.00')  # 100 + 50
        assert summary['total_income'] == Decimal('0.00')
        assert summary['total_transactions'] == 2
    
    def test_import_from_csv_basic(self, db_session, sample_account):
        """Test basic CSV import functionality."""
        service = TransactionService(db_session)
        
        csv_content = """description,amount,date,category
Grocery Store,-50.00,2024-01-01,food
Salary,2000.00,2024-01-01,salary
Gas Station,-30.00,2024-01-02,transportation"""
        
        imported_count, errors = service.import_from_csv(
            csv_content=csv_content,
            account_id=sample_account.id,
            skip_header=True
        )
        
        assert imported_count == 3
        assert len(errors) == 0
        
        # Verify transactions were created
        transactions = service.get_transactions(account_id=sample_account.id)
        assert len(transactions) == 3
    
    def test_import_from_csv_with_errors(self, db_session, sample_account):
        """Test CSV import with invalid data."""
        service = TransactionService(db_session)
        
        csv_content = """description,amount,date
Valid Transaction,-50.00,2024-01-01
Invalid Amount,invalid,2024-01-01
Missing Date,-30.00,
,50.00,2024-01-01"""
        
        imported_count, errors = service.import_from_csv(
            csv_content=csv_content,
            account_id=sample_account.id,
            skip_header=True
        )
        
        assert imported_count == 1  # Only one valid transaction
        assert len(errors) == 3  # Three error rows
    
    def test_export_to_csv(self, db_session, multiple_transactions):
        """Test CSV export functionality."""
        service = TransactionService(db_session)
        
        transactions = service.get_transactions()
        csv_content = service.export_to_csv(transactions, include_headers=True)
        
        assert isinstance(csv_content, str)
        assert 'description' in csv_content  # Header should be present
        assert 'Salary' in csv_content  # Transaction data should be present
        
        # Count lines (header + transactions)
        lines = csv_content.strip().split('\n')
        assert len(lines) == 5  # 1 header + 4 transactions
    
    def test_export_to_csv_no_headers(self, db_session, multiple_transactions):
        """Test CSV export without headers."""
        service = TransactionService(db_session)
        
        transactions = service.get_transactions()
        csv_content = service.export_to_csv(transactions, include_headers=False)
        
        assert isinstance(csv_content, str)
        assert 'description' not in csv_content  # No header
        
        # Count lines (transactions only)
        lines = csv_content.strip().split('\n')
        assert len(lines) == 4  # 4 transactions, no header
