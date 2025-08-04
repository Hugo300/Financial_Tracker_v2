"""
Stock and Holdings models for the Financial Tracker application.

This module defines models for managing stock information and portfolio holdings.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, String, Numeric, Date, DateTime, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class StockTransactionType(Enum):
    """Enumeration of stock transaction types."""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"


class Stock(BaseModel):
    """
    Model representing a stock/security.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., AAPL, GOOGL)
        name: Company name
        exchange: Stock exchange (e.g., NASDAQ, NYSE)
        sector: Business sector
        industry: Industry classification
        currency: Trading currency
        last_price: Last known price
        last_updated: When price was last updated
        description: Company description
    """
    
    __tablename__ = 'stocks'
    
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(100))
    currency = Column(String(3), nullable=False, default='USD')
    last_price = Column(Numeric(precision=15, scale=4))
    last_updated = Column(DateTime)
    description = Column(Text)
    
    # Relationships
    holdings = relationship(
        "Holding",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    transactions = relationship(
        "StockTransaction",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __init__(
        self,
        symbol: str,
        name: str,
        exchange: Optional[str] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        currency: str = 'USD',
        description: Optional[str] = None
    ):
        """
        Initialize a new Stock.
        
        Args:
            symbol: Stock ticker symbol
            name: Company name
            exchange: Stock exchange
            sector: Business sector
            industry: Industry classification
            currency: Trading currency
            description: Company description
        """
        self.symbol = symbol.upper()
        self.name = name
        self.exchange = exchange
        self.sector = sector
        self.industry = industry
        self.currency = currency
        self.description = description
    
    @property
    def formatted_price(self) -> str:
        """
        Get formatted last price.
        
        Returns:
            Formatted price string
        """
        if self.last_price is None:
            return "N/A"
        return f"${self.last_price:,.2f}"
    
    def update_price(self, price: Decimal) -> None:
        """
        Update the stock price.
        
        Args:
            price: New stock price
        """
        self.last_price = price
        self.last_updated = datetime.utcnow()
    
    def get_total_shares(self) -> Decimal:
        """
        Get total shares held across all holdings.
        
        Returns:
            Total number of shares
        """
        return sum(holding.shares for holding in self.holdings.all())
    
    def get_total_value(self) -> Decimal:
        """
        Get total value of all holdings for this stock.
        
        Returns:
            Total value based on current price
        """
        if self.last_price is None:
            return Decimal('0')
        return self.get_total_shares() * self.last_price
    
    def __repr__(self) -> str:
        """String representation of the stock."""
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class Holding(BaseModel):
    """
    Model representing a stock holding in a portfolio.
    
    Attributes:
        account_id: Foreign key to the brokerage account
        stock_id: Foreign key to the stock
        shares: Number of shares held
        average_cost: Average cost per share
        purchase_date: Date of initial purchase
        notes: Additional notes about the holding
    """
    
    __tablename__ = 'holdings'
    
    account_id = Column(ForeignKey('accounts.id'), nullable=False, index=True)
    stock_id = Column(ForeignKey('stocks.id'), nullable=False, index=True)
    shares = Column(Numeric(precision=15, scale=6), nullable=False, default=0)
    average_cost = Column(Numeric(precision=15, scale=4), nullable=False, default=0)
    purchase_date = Column(Date)
    notes = Column(Text)
    
    # Relationships
    account = relationship("Account")
    stock = relationship("Stock", back_populates="holdings")
    
    def __init__(
        self,
        account_id: int,
        stock_id: int,
        shares: Decimal,
        average_cost: Decimal,
        purchase_date: Optional[date] = None,
        notes: Optional[str] = None
    ):
        """
        Initialize a new Holding.
        
        Args:
            account_id: ID of the brokerage account
            stock_id: ID of the stock
            shares: Number of shares
            average_cost: Average cost per share
            purchase_date: Date of purchase
            notes: Additional notes
        """
        self.account_id = account_id
        self.stock_id = stock_id
        self.shares = shares
        self.average_cost = average_cost
        self.purchase_date = purchase_date or date.today()
        self.notes = notes
    
    @property
    def total_cost(self) -> Decimal:
        """
        Get total cost of the holding.
        
        Returns:
            Total cost (shares * average_cost)
        """
        return self.shares * self.average_cost
    
    @property
    def current_value(self) -> Decimal:
        """
        Get current value of the holding.
        
        Returns:
            Current value based on stock's last price
        """
        if self.stock.last_price is None:
            return Decimal('0')
        return self.shares * self.stock.last_price
    
    @property
    def gain_loss(self) -> Decimal:
        """
        Get gain/loss for the holding.
        
        Returns:
            Gain or loss amount
        """
        return self.current_value - self.total_cost
    
    @property
    def gain_loss_percentage(self) -> Decimal:
        """
        Get gain/loss percentage for the holding.
        
        Returns:
            Gain or loss percentage
        """
        if self.total_cost == 0:
            return Decimal('0')
        return (self.gain_loss / self.total_cost) * 100
    
    def update_shares(self, shares_change: Decimal, new_cost: Decimal) -> None:
        """
        Update shares and recalculate average cost.
        
        Args:
            shares_change: Change in shares (positive for buy, negative for sell)
            new_cost: Cost per share for the transaction
        """
        if shares_change > 0:  # Buying shares
            total_cost = (self.shares * self.average_cost) + (shares_change * new_cost)
            self.shares += shares_change
            if self.shares > 0:
                self.average_cost = total_cost / self.shares
        else:  # Selling shares
            self.shares += shares_change  # shares_change is negative
            if self.shares < 0:
                self.shares = Decimal('0')
    
    def __repr__(self) -> str:
        """String representation of the holding."""
        return f"<Holding(id={self.id}, stock='{self.stock.symbol}', shares={self.shares})>"


class StockTransaction(BaseModel):
    """
    Model representing a stock transaction (buy/sell/dividend).

    Attributes:
        account_id: Foreign key to the brokerage account
        stock_id: Foreign key to the stock
        transaction_type: Type of transaction (buy, sell, dividend, etc.)
        shares: Number of shares involved
        price_per_share: Price per share for the transaction
        total_amount: Total transaction amount
        fees: Transaction fees
        date: Date of the transaction
        notes: Additional notes
    """

    __tablename__ = 'stock_transactions'

    account_id = Column(ForeignKey('accounts.id'), nullable=False, index=True)
    stock_id = Column(ForeignKey('stocks.id'), nullable=False, index=True)
    transaction_type = Column(SQLEnum(StockTransactionType), nullable=False, index=True)
    shares = Column(Numeric(precision=15, scale=6), nullable=False)
    price_per_share = Column(Numeric(precision=15, scale=4), nullable=False)
    total_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    fees = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text)

    # Relationships
    account = relationship("Account")
    stock = relationship("Stock", back_populates="transactions")

    def __init__(
        self,
        account_id: int,
        stock_id: int,
        transaction_type: StockTransactionType,
        shares: Decimal,
        price_per_share: Decimal,
        date: date,
        fees: Decimal = Decimal('0'),
        notes: Optional[str] = None
    ):
        """
        Initialize a new StockTransaction.

        Args:
            account_id: ID of the brokerage account
            stock_id: ID of the stock
            transaction_type: Type of transaction
            shares: Number of shares
            price_per_share: Price per share
            date: Transaction date
            fees: Transaction fees
            notes: Additional notes
        """
        self.account_id = account_id
        self.stock_id = stock_id
        self.transaction_type = transaction_type
        self.shares = shares
        self.price_per_share = price_per_share
        self.date = date
        self.fees = fees
        self.notes = notes

        # Calculate total amount based on transaction type
        if transaction_type in [StockTransactionType.BUY, StockTransactionType.SELL]:
            self.total_amount = (shares * price_per_share) + fees
        else:  # Dividend or other
            self.total_amount = shares * price_per_share

    @property
    def formatted_total(self) -> str:
        """
        Get formatted total amount.

        Returns:
            Formatted total amount string
        """
        return f"${self.total_amount:,.2f}"

    def __repr__(self) -> str:
        """String representation of the stock transaction."""
        return f"<StockTransaction(id={self.id}, type={self.transaction_type.value}, shares={self.shares}, date={self.date})>"
