"""
Account model for the Financial Tracker application.

This module defines the Account model for managing different types of financial accounts.
"""

from enum import Enum
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Column, String, Numeric, Enum as SQLEnum, Boolean, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class AccountType(Enum):
    """Enumeration of supported account types."""
    
    CHECKING = "checking"
    SAVINGS = "savings"
    BROKERAGE = "brokerage"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    INVESTMENT = "investment"
    LOAN = "loan"
    OTHER = "other"


class Account(BaseModel):
    """
    Model representing a financial account.
    
    Attributes:
        name: Display name of the account
        account_type: Type of account (checking, savings, etc.)
        balance: Current balance of the account
        currency: Currency symbol for the account (default: $)
        description: Optional description of the account
        is_active: Whether the account is currently active
        institution: Name of the financial institution
        account_number: Last 4 digits or identifier for the account
    """
    
    __tablename__ = 'accounts'
    
    name = Column(String(100), nullable=False, index=True)
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    balance = Column(Numeric(precision=15, scale=2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default='$')
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    institution = Column(String(100))
    account_number = Column(String(20))
    
    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __init__(
        self,
        name: str,
        account_type: AccountType,
        balance: Decimal = Decimal('0.00'),
        currency: str = '$',
        description: Optional[str] = None,
        institution: Optional[str] = None,
        account_number: Optional[str] = None,
        is_active: bool = True
    ):
        """
        Initialize a new Account.
        
        Args:
            name: Display name of the account
            account_type: Type of account
            balance: Initial balance (default: 0.00)
            currency: Currency symbol (default: $)
            description: Optional description
            institution: Financial institution name
            account_number: Account identifier
            is_active: Whether account is active (default: True)
        """
        self.name = name
        self.account_type = account_type
        self.balance = balance
        self.currency = currency
        self.description = description
        self.institution = institution
        self.account_number = account_number
        self.is_active = is_active
    
    @property
    def formatted_balance(self) -> str:
        """
        Get formatted balance with currency symbol.
        
        Returns:
            Formatted balance string
        """
        return f"{self.currency}{self.balance:,.2f}"
    
    @property
    def display_name(self) -> str:
        """
        Get display name with institution if available.
        
        Returns:
            Formatted display name
        """
        if self.institution:
            return f"{self.name} ({self.institution})"
        return self.name
    
    def update_balance(self, amount: Decimal) -> None:
        """
        Update account balance by adding the specified amount.
        
        Args:
            amount: Amount to add to balance (can be negative)
        """
        self.balance += amount
    
    def get_transaction_count(self) -> int:
        """
        Get the total number of transactions for this account.
        
        Returns:
            Number of transactions
        """
        return self.transactions.count()
    
    def get_recent_transactions(self, limit: int = 10) -> List['Transaction']:
        """
        Get recent transactions for this account.

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List of recent transactions
        """
        from .transaction import Transaction
        return (
            self.transactions
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_income_total(self) -> Decimal:
        """
        Get total income for this account.

        Returns:
            Total income amount
        """
        from .transaction import Transaction, TransactionType
        result = (
            self.transactions
            .filter(Transaction.transaction_type == TransactionType.INCOME)
            .with_entities(Transaction.amount)
            .all()
        )
        return sum(row[0] for row in result) if result else Decimal('0.00')

    def get_expense_total(self) -> Decimal:
        """
        Get total expenses for this account.

        Returns:
            Total expense amount
        """
        from .transaction import Transaction, TransactionType
        result = (
            self.transactions
            .filter(Transaction.transaction_type == TransactionType.EXPENSE)
            .with_entities(Transaction.amount)
            .all()
        )
        return sum(row[0] for row in result) if result else Decimal('0.00')
    
    def __repr__(self) -> str:
        """String representation of the account."""
        return f"<Account(id={self.id}, name='{self.name}', type={self.account_type.value}, balance={self.balance})>"
