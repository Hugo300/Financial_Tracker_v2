"""
Transaction model for the Financial Tracker application.

This module defines the Transaction model for managing financial transactions.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class TransactionType(Enum):
    """Enumeration of transaction types."""
    
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    ADJUSTMENT = "adjustment"


class TransactionCategory(Enum):
    """Enumeration of common transaction categories."""
    
    # Income categories
    SALARY = "salary"
    FREELANCE = "freelance"
    INVESTMENT_INCOME = "investment_income"
    BUSINESS_INCOME = "business_income"
    OTHER_INCOME = "other_income"
    
    # Expense categories
    FOOD = "food"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    EDUCATION = "education"
    INSURANCE = "insurance"
    TAXES = "taxes"
    DEBT_PAYMENT = "debt_payment"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CHARITY = "charity"
    OTHER_EXPENSE = "other_expense"
    
    # Transfer categories
    ACCOUNT_TRANSFER = "account_transfer"
    
    # Investment categories
    STOCK_PURCHASE = "stock_purchase"
    STOCK_SALE = "stock_sale"
    DIVIDEND_PAYMENT = "dividend_payment"
    
    # Other
    UNCATEGORIZED = "uncategorized"


class Transaction(BaseModel):
    """
    Model representing a financial transaction.
    
    Attributes:
        account_id: Foreign key to the associated account
        amount: Transaction amount (positive for income, negative for expenses)
        transaction_type: Type of transaction
        category: Category of the transaction
        description: Description of the transaction
        date: Date when the transaction occurred
        payee: Who the transaction was paid to/received from
        reference: Reference number or check number
        tags: Comma-separated tags for additional categorization
        is_recurring: Whether this is a recurring transaction
        notes: Additional notes about the transaction
    """
    
    __tablename__ = 'transactions'
    
    account_id = Column(ForeignKey('accounts.id'), nullable=False, index=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    category = Column(SQLEnum(TransactionCategory), nullable=False, default=TransactionCategory.UNCATEGORIZED, index=True)
    description = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    payee = Column(String(100))
    reference = Column(String(50))
    tags = Column(String(255))
    is_recurring = Column(Boolean, nullable=False, default=False)
    notes = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __init__(
        self,
        account_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        date: date,
        category: TransactionCategory = TransactionCategory.UNCATEGORIZED,
        payee: Optional[str] = None,
        reference: Optional[str] = None,
        tags: Optional[str] = None,
        is_recurring: bool = False,
        notes: Optional[str] = None
    ):
        """
        Initialize a new Transaction.
        
        Args:
            account_id: ID of the associated account
            amount: Transaction amount
            transaction_type: Type of transaction
            description: Transaction description
            date: Transaction date
            category: Transaction category
            payee: Payee name
            reference: Reference number
            tags: Comma-separated tags
            is_recurring: Whether transaction is recurring
            notes: Additional notes
        """
        self.account_id = account_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description
        self.date = date
        self.category = category
        self.payee = payee
        self.reference = reference
        self.tags = tags
        self.is_recurring = is_recurring
        self.notes = notes
    
    @property
    def formatted_amount(self) -> str:
        """
        Get formatted amount with currency symbol.
        
        Returns:
            Formatted amount string
        """
        currency = self.account.currency if self.account else '$'
        return f"{currency}{abs(self.amount):,.2f}"
    
    @property
    def is_income(self) -> bool:
        """Check if transaction is income (positive amount)."""
        return self.amount > 0
    
    @property
    def is_expense(self) -> bool:
        """Check if transaction is expense (negative amount)."""
        return self.amount < 0
    
    @property
    def tag_list(self) -> list:
        """
        Get tags as a list.
        
        Returns:
            List of tags
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the transaction.
        
        Args:
            tag: Tag to add
        """
        current_tags = self.tag_list
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the transaction.
        
        Args:
            tag: Tag to remove
        """
        current_tags = self.tag_list
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ', '.join(current_tags) if current_tags else None
    
    def __repr__(self) -> str:
        """String representation of the transaction."""
        return f"<Transaction(id={self.id}, amount={self.amount}, description='{self.description}', date={self.date})>"
