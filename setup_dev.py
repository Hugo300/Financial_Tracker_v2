#!/usr/bin/env python3
"""
Development setup script for Financial Tracker.

This script helps set up the development environment and creates sample data
for testing and development purposes.
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta
import random

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.web.app import create_app
from src.models import db, AccountType, TransactionType, TransactionCategory, StockTransactionType
from src.services import AccountService, TransactionService, StockService


def create_sample_accounts(account_service):
    """Create sample accounts for development."""
    print("Creating sample accounts...")
    
    accounts = [
        {
            'name': 'Primary Checking',
            'account_type': AccountType.CHECKING,
            'balance': Decimal('2500.00'),
            'institution': 'First National Bank',
            'account_number': '1234',
            'description': 'Main checking account for daily expenses'
        },
        {
            'name': 'High Yield Savings',
            'account_type': AccountType.SAVINGS,
            'balance': Decimal('15000.00'),
            'institution': 'Online Savings Bank',
            'account_number': '5678',
            'description': 'Emergency fund and savings'
        },
        {
            'name': 'Investment Account',
            'account_type': AccountType.BROKERAGE,
            'balance': Decimal('25000.00'),
            'institution': 'Investment Brokerage',
            'account_number': '9012',
            'description': 'Long-term investment portfolio'
        },
        {
            'name': 'Credit Card',
            'account_type': AccountType.CREDIT_CARD,
            'balance': Decimal('-1200.00'),
            'institution': 'Credit Union',
            'account_number': '3456',
            'description': 'Primary credit card'
        }
    ]
    
    created_accounts = []
    for account_data in accounts:
        account = account_service.create_account(**account_data)
        created_accounts.append(account)
        print(f"  Created: {account.name}")
    
    return created_accounts


def create_sample_transactions(transaction_service, accounts):
    """Create sample transactions for development."""
    print("Creating sample transactions...")
    
    checking_account = next(acc for acc in accounts if acc.account_type == AccountType.CHECKING)
    credit_card = next(acc for acc in accounts if acc.account_type == AccountType.CREDIT_CARD)
    
    # Sample transactions for the last 30 days
    base_date = date.today() - timedelta(days=30)
    
    transactions = [
        # Income
        (checking_account.id, Decimal('3000.00'), TransactionType.INCOME, 'Monthly Salary', TransactionCategory.SALARY, 'Employer Inc.'),
        (checking_account.id, Decimal('500.00'), TransactionType.INCOME, 'Freelance Project', TransactionCategory.FREELANCE, 'Client ABC'),
        
        # Regular expenses
        (checking_account.id, Decimal('-1200.00'), TransactionType.EXPENSE, 'Rent Payment', TransactionCategory.HOUSING, 'Property Management'),
        (checking_account.id, Decimal('-150.00'), TransactionType.EXPENSE, 'Electric Bill', TransactionCategory.UTILITIES, 'Power Company'),
        (checking_account.id, Decimal('-80.00'), TransactionType.EXPENSE, 'Internet Bill', TransactionCategory.UTILITIES, 'ISP Provider'),
        (checking_account.id, Decimal('-300.00'), TransactionType.EXPENSE, 'Groceries', TransactionCategory.FOOD, 'Supermarket'),
        (checking_account.id, Decimal('-60.00'), TransactionType.EXPENSE, 'Gas Station', TransactionCategory.TRANSPORTATION, 'Gas Station'),
        (checking_account.id, Decimal('-45.00'), TransactionType.EXPENSE, 'Restaurant Dinner', TransactionCategory.FOOD, 'Italian Restaurant'),
        
        # Credit card transactions
        (credit_card.id, Decimal('-120.00'), TransactionType.EXPENSE, 'Online Shopping', TransactionCategory.SHOPPING, 'E-commerce Store'),
        (credit_card.id, Decimal('-25.00'), TransactionType.EXPENSE, 'Coffee Shop', TransactionCategory.FOOD, 'Local Cafe'),
        (credit_card.id, Decimal('-200.00'), TransactionType.EXPENSE, 'Clothing Purchase', TransactionCategory.SHOPPING, 'Department Store'),
        
        # Entertainment and misc
        (checking_account.id, Decimal('-15.00'), TransactionType.EXPENSE, 'Movie Tickets', TransactionCategory.ENTERTAINMENT, 'Cinema'),
        (checking_account.id, Decimal('-100.00'), TransactionType.EXPENSE, 'Gym Membership', TransactionCategory.HEALTHCARE, 'Fitness Center'),
        (checking_account.id, Decimal('-50.00'), TransactionType.EXPENSE, 'Phone Bill', TransactionCategory.UTILITIES, 'Mobile Carrier'),
    ]
    
    created_transactions = []
    for i, (account_id, amount, t_type, description, category, payee) in enumerate(transactions):
        transaction_date = base_date + timedelta(days=random.randint(0, 29))
        
        transaction = transaction_service.create_transaction(
            account_id=account_id,
            amount=amount,
            transaction_type=t_type,
            description=description,
            transaction_date=transaction_date,
            category=category,
            payee=payee,
            update_balance=False  # Don't update balance to keep sample balances
        )
        created_transactions.append(transaction)
    
    print(f"  Created {len(created_transactions)} transactions")
    return created_transactions


def create_sample_stocks(stock_service, brokerage_account):
    """Create sample stocks and holdings for development."""
    print("Creating sample stocks and holdings...")
    
    stocks_data = [
        ('AAPL', 'Apple Inc.', Decimal('150.00')),
        ('GOOGL', 'Alphabet Inc.', Decimal('2500.00')),
        ('MSFT', 'Microsoft Corporation', Decimal('300.00')),
        ('TSLA', 'Tesla Inc.', Decimal('200.00')),
        ('AMZN', 'Amazon.com Inc.', Decimal('3000.00')),
    ]
    
    created_stocks = []
    for symbol, name, price in stocks_data:
        stock = stock_service.create_stock(
            symbol=symbol,
            name=name,
            fetch_info=False
        )
        
        # Set sample price
        stock.last_price = price
        db.session.commit()
        
        created_stocks.append(stock)
        print(f"  Created stock: {symbol}")
    
    # Create sample holdings
    holdings_data = [
        (0, Decimal('10.0'), Decimal('145.00')),  # AAPL
        (1, Decimal('2.0'), Decimal('2400.00')),  # GOOGL
        (2, Decimal('15.0'), Decimal('280.00')),  # MSFT
        (3, Decimal('5.0'), Decimal('180.00')),   # TSLA
        (4, Decimal('1.0'), Decimal('2800.00')),  # AMZN
    ]
    
    for stock_idx, shares, avg_cost in holdings_data:
        stock = created_stocks[stock_idx]
        
        # Create stock transaction
        stock_service.create_stock_transaction(
            account_id=brokerage_account.id,
            stock_id=stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=shares,
            price_per_share=avg_cost,
            transaction_date=date.today() - timedelta(days=random.randint(30, 365)),
            fees=Decimal('9.99'),
            update_holding=True
        )
        
        print(f"  Created holding: {shares} shares of {stock.symbol}")
    
    return created_stocks


def setup_development_environment():
    """Set up the complete development environment."""
    print("Setting up Financial Tracker development environment...")
    print("=" * 50)
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        
        # Initialize services
        account_service = AccountService()
        transaction_service = TransactionService()
        stock_service = StockService()
        
        # Create sample data
        accounts = create_sample_accounts(account_service)
        transactions = create_sample_transactions(transaction_service, accounts)
        
        # Find brokerage account for stocks
        brokerage_account = next(acc for acc in accounts if acc.account_type == AccountType.BROKERAGE)
        stocks = create_sample_stocks(stock_service, brokerage_account)
        
        print("\n" + "=" * 50)
        print("Development environment setup complete!")
        print("\nSample data created:")
        print(f"  - {len(accounts)} accounts")
        print(f"  - {len(transactions)} transactions")
        print(f"  - {len(stocks)} stocks with holdings")
        print("\nYou can now run the application with:")
        print("  python main.py")
        print("\nThen visit: http://localhost:5000")


if __name__ == '__main__':
    setup_development_environment()
