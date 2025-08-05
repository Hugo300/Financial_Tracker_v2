"""
Account service for managing financial accounts.

This module provides business logic for account operations including
CRUD operations, balance management, and account analytics.
"""

import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, UTC

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import db, Account, AccountType, Transaction, TransactionType

logger = logging.getLogger(__name__)


class AccountService:
    """Service class for managing financial accounts."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the account service.
        
        Args:
            session: Database session (uses db.session if not provided)
        """
        self.session = session or db.session
    
    def create_account(
        self,
        name: str,
        account_type: AccountType,
        balance: Decimal = Decimal('0.00'),
        currency: str = '$',
        description: Optional[str] = None,
        institution: Optional[str] = None,
        account_number: Optional[str] = None,
        is_active: bool = True
    ) -> Account:
        """
        Create a new account.
        
        Args:
            name: Account name
            account_type: Type of account
            balance: Initial balance
            currency: Currency symbol
            description: Account description
            institution: Financial institution
            account_number: Account number/identifier
            is_active: Whether account is active
            
        Returns:
            Created account instance
        """
        try:
            account = Account(
                name=name,
                account_type=account_type,
                balance=balance,
                currency=currency,
                description=description,
                institution=institution,
                account_number=account_number,
                is_active=is_active
            )
            
            self.session.add(account)
            self.session.commit()
            
            logger.info(f"Created account: {account.name} ({account.account_type.value})")
            return account
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating account: {e}")
            raise
    
    def get_account(self, account_id: int) -> Optional[Account]:
        """
        Get account by ID.
        
        Args:
            account_id: Account ID
            
        Returns:
            Account instance or None if not found
        """
        return self.session.query(Account).filter(Account.id == account_id).first()
    
    def get_accounts(
        self,
        account_type: Optional[AccountType] = None,
        is_active: Optional[bool] = None,
        institution: Optional[str] = None
    ) -> List[Account]:
        """
        Get accounts with optional filtering.
        
        Args:
            account_type: Filter by account type
            is_active: Filter by active status
            institution: Filter by institution
            
        Returns:
            List of accounts matching criteria
        """
        query = self.session.query(Account)
        
        if account_type is not None:
            query = query.filter(Account.account_type == account_type)
        
        if is_active is not None:
            query = query.filter(Account.is_active == is_active)
        
        if institution is not None:
            query = query.filter(Account.institution == institution)
        
        return query.order_by(Account.name).all()
    
    def update_account(
        self,
        account_id: int,
        **kwargs
    ) -> Optional[Account]:
        """
        Update account information.
        
        Args:
            account_id: Account ID
            **kwargs: Fields to update
            
        Returns:
            Updated account or None if not found
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return None
            
            # Update allowed fields
            allowed_fields = {
                'name', 'description', 'institution', 'account_number',
                'is_active', 'currency'
            }
            
            for key, value in kwargs.items():
                if key in allowed_fields and hasattr(account, key):
                    setattr(account, key, value)
            
            account.updated_at = datetime.now(UTC)
            self.session.commit()
            
            logger.info(f"Updated account {account_id}")
            return account
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating account {account_id}: {e}")
            raise
    
    def delete_account(self, account_id: int) -> bool:
        """
        Delete an account (soft delete by setting is_active=False).
        
        Args:
            account_id: Account ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            
            # Check if account has transactions
            transaction_count = account.get_transaction_count()
            if transaction_count > 0:
                # Soft delete - just deactivate
                account.is_active = False
                logger.info(f"Deactivated account {account_id} (has {transaction_count} transactions)")
            else:
                # Hard delete if no transactions
                self.session.delete(account)
                logger.info(f"Deleted account {account_id}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting account {account_id}: {e}")
            raise
    
    def update_balance(self, account_id: int, amount: Decimal) -> Optional[Account]:
        """
        Update account balance.
        
        Args:
            account_id: Account ID
            amount: Amount to add to balance (can be negative)
            
        Returns:
            Updated account or None if not found
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return None
            
            old_balance = account.balance
            account.update_balance(amount)
            account.updated_at = datetime.now(UTC)
            
            self.session.commit()
            
            logger.info(f"Updated balance for account {account_id}: {old_balance} -> {account.balance}")
            return account
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating balance for account {account_id}: {e}")
            raise
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all accounts.
        
        Returns:
            Dictionary with account summary data
        """
        try:
            # Get total balances by account type
            balances_by_type = (
                self.session.query(
                    Account.account_type,
                    func.sum(Account.balance).label('total_balance'),
                    func.count(Account.id).label('account_count')
                )
                .filter(Account.is_active == True)
                .group_by(Account.account_type)
                .all()
            )
            
            # Calculate totals
            total_assets = Decimal('0')
            total_liabilities = Decimal('0')
            account_counts = {}
            balances = {}
            
            for account_type, balance, count in balances_by_type:
                balances[account_type.value] = balance or Decimal('0')
                account_counts[account_type.value] = count
                
                # Categorize as asset or liability
                if account_type in [AccountType.CREDIT_CARD, AccountType.LOAN]:
                    total_liabilities += abs(balance or Decimal('0'))
                else:
                    total_assets += balance or Decimal('0')
            
            net_worth = total_assets - total_liabilities
            
            return {
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'net_worth': net_worth,
                'account_counts': account_counts,
                'balances_by_type': balances,
                'total_accounts': sum(account_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {
                'total_assets': Decimal('0'),
                'total_liabilities': Decimal('0'),
                'net_worth': Decimal('0'),
                'account_counts': {},
                'balances_by_type': {},
                'total_accounts': 0
            }
    
    def get_balance_history(
        self,
        account_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get balance history for an account over specified days.
        
        Args:
            account_id: Account ID
            days: Number of days to look back
            
        Returns:
            List of balance history records
        """
        try:
            account = self.get_account(account_id)
            if not account:
                return []
            
            start_date = date.today() - timedelta(days=days)
            
            # Get transactions for the period
            transactions = (
                self.session.query(Transaction)
                .filter(
                    Transaction.account_id == account_id,
                    Transaction.date >= start_date
                )
                .order_by(Transaction.date, Transaction.created_at)
                .all()
            )
            
            # Calculate running balance
            current_balance = account.balance
            history = []
            
            # Work backwards from current balance
            for transaction in reversed(transactions):
                history.insert(0, {
                    'date': transaction.date,
                    'balance': current_balance,
                    'transaction_amount': transaction.amount,
                    'description': transaction.description
                })
                current_balance -= transaction.amount
            
            # Add starting balance if we have transactions
            if transactions:
                history.insert(0, {
                    'date': start_date,
                    'balance': current_balance,
                    'transaction_amount': None,
                    'description': 'Starting balance'
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting balance history for account {account_id}: {e}")
            return []
