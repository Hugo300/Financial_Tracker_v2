"""
Test configuration and fixtures for the Financial Tracker application.

This module provides pytest fixtures and configuration for testing.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from flask import Flask

# Add src directory to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from src.config import get_config
from src.web.app import create_app
from src.models import db, Account, AccountType, Transaction, TransactionType, TransactionCategory
from src.models import Stock, Holding, StockTransaction, StockTransactionType, UserSettings

#TODO: Add ui tests for other pages now that we have a validated example for stocks main page
#TODO: Expand stock ui tests

@pytest.fixture(scope='session')
def app() -> Flask:
    """Create application for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Set test configuration
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

    # Get host and port from environment or use defaults
    config = get_config('testing')
    os.environ["FLASK_HOST"] = str(config.FLASK_HOST)
    os.environ["FLASK_PORT"] = str(config.FLASK_PORT)
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create default user settings
        settings = UserSettings.get_default_settings()
        db.session.add(settings)
        db.session.commit()
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Create database session for testing with clean state for each test."""
    with app.app_context():
        # Create all tables
        db.create_all()

        yield db.session

        # Clean up after test by removing all data
        db.session.rollback()

        # Delete all data from tables (in reverse order to handle foreign keys)
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())

        db.session.commit()
        db.session.remove()

# Configuration for pytest-playwright
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

@pytest.fixture
def sample_account(db_session):
    """Create a sample account for testing."""
    account = Account(
        name="Test Checking Account",
        account_type=AccountType.CHECKING,
        balance=Decimal('1000.00'),
        currency='$',
        description="Test account for unit tests",
        institution="Test Bank",
        account_number="1234",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_brokerage_account(db_session):
    """Create a sample brokerage account for testing."""
    account = Account(
        name="Test Brokerage Account",
        account_type=AccountType.BROKERAGE,
        balance=Decimal('10000.00'),
        currency='$',
        description="Test brokerage account",
        institution="Test Brokerage",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_transaction(db_session, sample_account):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        account_id=sample_account.id,
        amount=Decimal('-50.00'),
        transaction_type=TransactionType.EXPENSE,
        description="Test grocery purchase",
        date=date.today(),
        category=TransactionCategory.FOOD,
        payee="Test Store",
        reference="TXN123",
        tags="groceries, food",
        notes="Weekly grocery shopping"
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


@pytest.fixture
def sample_stock(db_session):
    """Create a sample stock for testing."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
        description="Apple Inc. designs, manufactures, and markets smartphones."
    )
    stock.last_price = Decimal('150.00')
    stock.last_updated = datetime.now(timezone.utc)

    db_session.add(stock)
    db_session.commit()
    return stock


@pytest.fixture
def sample_holding(db_session, sample_brokerage_account, sample_stock):
    """Create a sample stock holding for testing."""
    holding = Holding(
        account_id=sample_brokerage_account.id,
        stock_id=sample_stock.id,
        shares=Decimal('10.0'),
        average_cost=Decimal('140.00'),
        purchase_date=date.today(),
        notes="Test holding"
    )
    db_session.add(holding)
    db_session.commit()
    return holding


@pytest.fixture
def sample_stock_transaction(db_session, sample_brokerage_account, sample_stock):
    """Create a sample stock transaction for testing."""
    transaction = StockTransaction(
        account_id=sample_brokerage_account.id,
        stock_id=sample_stock.id,
        transaction_type=StockTransactionType.BUY,
        shares=Decimal('5.0'),
        price_per_share=Decimal('145.00'),
        date=date.today(),
        fees=Decimal('9.99'),
        notes="Test stock purchase"
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


@pytest.fixture
def multiple_accounts(db_session):
    """Create multiple accounts for testing."""
    accounts = [
        Account(
            name="Checking Account",
            account_type=AccountType.CHECKING,
            balance=Decimal('2500.00'),
            currency='$',
            is_active=True
        ),
        Account(
            name="Savings Account",
            account_type=AccountType.SAVINGS,
            balance=Decimal('15000.00'),
            currency='$',
            is_active=True
        ),
        Account(
            name="Credit Card",
            account_type=AccountType.CREDIT_CARD,
            balance=Decimal('-1200.00'),
            currency='$',
            is_active=True
        ),
        Account(
            name="Investment Account",
            account_type=AccountType.BROKERAGE,
            balance=Decimal('25000.00'),
            currency='$',
            is_active=True
        ),
        Account(
            name="Old Account",
            account_type=AccountType.CHECKING,
            balance=Decimal('0.00'),
            currency='$',
            is_active=False
        )
    ]
    
    for account in accounts:
        db_session.add(account)
    
    db_session.commit()
    return accounts


@pytest.fixture
def multiple_transactions(db_session, sample_account):
    """Create multiple transactions for testing."""
    transactions = [
        Transaction(
            account_id=sample_account.id,
            amount=Decimal('2000.00'),
            transaction_type=TransactionType.INCOME,
            description="Salary",
            date=date(2024, 1, 1),
            category=TransactionCategory.SALARY
        ),
        Transaction(
            account_id=sample_account.id,
            amount=Decimal('-500.00'),
            transaction_type=TransactionType.EXPENSE,
            description="Rent",
            date=date(2024, 1, 1),
            category=TransactionCategory.HOUSING
        ),
        Transaction(
            account_id=sample_account.id,
            amount=Decimal('-100.00'),
            transaction_type=TransactionType.EXPENSE,
            description="Groceries",
            date=date(2024, 1, 2),
            category=TransactionCategory.FOOD
        ),
        Transaction(
            account_id=sample_account.id,
            amount=Decimal('-50.00'),
            transaction_type=TransactionType.EXPENSE,
            description="Gas",
            date=date(2024, 1, 3),
            category=TransactionCategory.TRANSPORTATION
        )
    ]
    
    for transaction in transactions:
        db_session.add(transaction)
    
    db_session.commit()
    return transactions


# Mock data for testing
@pytest.fixture
def mock_stock_data():
    """Mock stock data for API testing."""
    return {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'exchange': 'NASDAQ',
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'currency': 'USD',
        'description': 'Apple Inc. designs, manufactures, and markets smartphones.',
        'market_cap': 2500000000000,
        'pe_ratio': 25.5,
        'dividend_yield': 0.005
    }


@pytest.fixture
def mock_historical_data():
    """Mock historical price data for testing."""
    return [
        {
            'date': date(2024, 1, 1),
            'open': 148.0,
            'high': 152.0,
            'low': 147.0,
            'close': 150.0,
            'volume': 50000000
        },
        {
            'date': date(2024, 1, 2),
            'open': 150.0,
            'high': 155.0,
            'low': 149.0,
            'close': 153.0,
            'volume': 45000000
        }
    ]
