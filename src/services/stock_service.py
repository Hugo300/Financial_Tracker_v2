"""
Stock service for managing stock holdings and transactions.

This module provides business logic for stock operations including
portfolio management, stock data updates, and investment tracking.
"""

import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import db, Stock, Holding, StockTransaction, StockTransactionType, Account
from .financial_data import FinancialDataService

logger = logging.getLogger(__name__)


class StockService:
    """Service class for managing stocks and holdings."""
    
    def __init__(self, session: Optional[Session] = None, financial_data_service: Optional[FinancialDataService] = None):
        """
        Initialize the stock service.
        
        Args:
            session: Database session (uses db.session if not provided)
            financial_data_service: Financial data service for price updates
        """
        self.session = session or db.session
        self.financial_data_service = financial_data_service or FinancialDataService()
    
    def create_stock(
        self,
        symbol: str,
        name: str,
        exchange: Optional[str] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        currency: str = 'USD',
        description: Optional[str] = None,
        fetch_info: bool = True
    ) -> Stock:
        """
        Create a new stock entry.
        
        Args:
            symbol: Stock ticker symbol
            name: Company name
            exchange: Stock exchange
            sector: Business sector
            industry: Industry classification
            currency: Trading currency
            description: Company description
            fetch_info: Whether to fetch additional info from API
            
        Returns:
            Created stock instance
        """
        try:
            # Check if stock already exists
            existing_stock = self.get_stock_by_symbol(symbol)
            if existing_stock:
                logger.info(f"Stock {symbol} already exists")
                return existing_stock
            
            stock = Stock(
                symbol=symbol,
                name=name,
                exchange=exchange,
                sector=sector,
                industry=industry,
                currency=currency,
                description=description
            )
            
            # Fetch additional information if requested
            if fetch_info:
                stock_info = self.financial_data_service.get_stock_info(symbol)
                if stock_info:
                    stock.name = stock_info.get('name', name)
                    stock.exchange = stock_info.get('exchange', exchange)
                    stock.sector = stock_info.get('sector', sector)
                    stock.industry = stock_info.get('industry', industry)
                    stock.description = stock_info.get('description', description)
            
            # Get current price
            current_price = self.financial_data_service.get_stock_price(symbol)
            if current_price:
                stock.update_price(current_price)
            
            self.session.add(stock)
            self.session.commit()
            
            logger.info(f"Created stock: {symbol} - {name}")
            return stock
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating stock {symbol}: {e}")
            raise
    
    def get_stock(self, stock_id: int) -> Optional[Stock]:
        """
        Get stock by ID.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            Stock instance or None if not found
        """
        return self.session.query(Stock).filter(Stock.id == stock_id).first()
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """
        Get stock by symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Stock instance or None if not found
        """
        return self.session.query(Stock).filter(Stock.symbol == symbol.upper()).first() # type: ignore [reportArgumentTypeIssue]
    
    def get_stocks(self, limit: Optional[int] = None, offset: int = 0) -> List[Stock]:
        """
        Get all stocks with optional pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of stocks
        """
        query = self.session.query(Stock).order_by(Stock.symbol)
        
        if offset > 0:
            query = query.offset(offset)
        
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
    
    def update_stock_price(self, stock_id: int) -> Optional[Stock]:
        """
        Update stock price from financial data service.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            Updated stock or None if not found
        """
        try:
            stock = self.get_stock(stock_id)
            if not stock:
                return None
            
            current_price = self.financial_data_service.get_stock_price(stock.symbol) # type: ignore [reportArgumentTypeIssue]
            if current_price:
                stock.update_price(current_price)
                self.session.commit()
                logger.info(f"Updated price for {stock.symbol}: ${current_price}")
            else:
                logger.warning(f"Could not fetch price for {stock.symbol}")
            
            return stock
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating stock price for {stock_id}: {e}")
            raise
    
    def update_all_stock_prices(self) -> Dict[str, bool]:
        """
        Update prices for all stocks.
        
        Returns:
            Dictionary mapping symbols to success status
        """
        stocks = self.get_stocks()
        results = {}
        
        for stock in stocks:
            try:
                updated_stock = self.update_stock_price(stock.id) # type: ignore [reportArgumentTypeIssue]
                results[stock.symbol] = updated_stock is not None
            except Exception as e:
                logger.error(f"Failed to update price for {stock.symbol}: {e}")
                results[stock.symbol] = False
        
        return results
    
    def create_holding(
        self,
        account_id: int,
        stock_id: int,
        shares: Decimal,
        average_cost: Decimal,
        purchase_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Holding:
        """
        Create a new stock holding.
        
        Args:
            account_id: Brokerage account ID
            stock_id: Stock ID
            shares: Number of shares
            average_cost: Average cost per share
            purchase_date: Date of purchase
            notes: Additional notes
            
        Returns:
            Created holding instance
        """
        try:
            holding = Holding(
                account_id=account_id,
                stock_id=stock_id,
                shares=shares,
                average_cost=average_cost,
                purchase_date=purchase_date,
                notes=notes
            )
            
            self.session.add(holding)
            self.session.commit()
            
            logger.info(f"Created holding: {shares} shares at ${average_cost}")
            return holding
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating holding: {e}")
            raise
    
    def get_holding(self, holding_id: int) -> Optional[Holding]:
        """
        Get holding by ID.
        
        Args:
            holding_id: Holding ID
            
        Returns:
            Holding instance or None if not found
        """
        return self.session.query(Holding).filter(Holding.id == holding_id).first()
    
    def get_holdings(
        self,
        account_id: Optional[int] = None,
        stock_id: Optional[int] = None
    ) -> List[Holding]:
        """
        Get holdings with optional filtering.
        
        Args:
            account_id: Filter by account ID
            stock_id: Filter by stock ID
            
        Returns:
            List of holdings
        """
        query = self.session.query(Holding)
        
        if account_id is not None:
            query = query.filter(Holding.account_id == account_id) # type: ignore [reportArgumentTypeIssue]
        
        if stock_id is not None:
            query = query.filter(Holding.stock_id == stock_id) # type: ignore [reportArgumentTypeIssue]
        
        return query.all()
    
    def create_stock_transaction(
        self,
        account_id: int,
        stock_id: int,
        transaction_type: StockTransactionType,
        shares: Decimal,
        price_per_share: Decimal,
        transaction_date: date,
        fees: Decimal = Decimal('0'),
        notes: Optional[str] = None,
        update_holding: bool = True
    ) -> StockTransaction:
        """
        Create a stock transaction and optionally update holdings.
        
        Args:
            account_id: Brokerage account ID
            stock_id: Stock ID
            transaction_type: Type of transaction
            shares: Number of shares
            price_per_share: Price per share
            transaction_date: Transaction date
            fees: Transaction fees
            notes: Additional notes
            update_holding: Whether to update holdings
            
        Returns:
            Created stock transaction
        """
        try:
            transaction = StockTransaction(
                account_id=account_id,
                stock_id=stock_id,
                transaction_type=transaction_type,
                shares=shares,
                price_per_share=price_per_share,
                date=transaction_date,
                fees=fees,
                notes=notes
            )
            
            self.session.add(transaction)
            
            # Update holdings if requested
            if update_holding and transaction_type in [StockTransactionType.BUY, StockTransactionType.SELL]:
                self._update_holding_from_transaction(transaction)
            
            self.session.commit()
            
            logger.info(f"Created stock transaction: {transaction_type.value} {shares} shares at ${price_per_share}")
            return transaction
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating stock transaction: {e}")
            raise
    
    def _update_holding_from_transaction(self, transaction: StockTransaction) -> None:
        """Update holding based on stock transaction."""
        # Find existing holding
        holding = (
            self.session.query(Holding)
            .filter(
                Holding.account_id == transaction.account_id, # type: ignore [reportArgumentTypeIssue]
                Holding.stock_id == transaction.stock_id # type: ignore [reportArgumentTypeIssue]
            )
            .first()
        )
        
        if transaction.transaction_type == StockTransactionType.BUY: # type: ignore [reportArgumentTypeIssue]
            if holding:
                # Update existing holding
                holding.update_shares(transaction.shares, transaction.price_per_share) # type: ignore [reportArgumentTypeIssue]
            else:
                # Create new holding
                holding = Holding(
                    account_id=transaction.account_id, # type: ignore [reportArgumentTypeIssue]
                    stock_id=transaction.stock_id, # type: ignore [reportArgumentTypeIssue]
                    shares=transaction.shares, # type: ignore [reportArgumentTypeIssue]
                    average_cost=transaction.price_per_share, # type: ignore [reportArgumentTypeIssue]
                    purchase_date=transaction.date # type: ignore [reportArgumentTypeIssue]
                )
                self.session.add(holding)
        
        elif transaction.transaction_type == StockTransactionType.SELL and holding: # type: ignore [reportArgumentTypeIssue]
            # Update holding for sale
            holding.update_shares(-transaction.shares, transaction.price_per_share) # type: ignore [reportArgumentTypeIssue]
            
            # Remove holding if no shares left
            if holding.shares <= 0:
                self.session.delete(holding)

    def get_portfolio_summary(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get portfolio summary with total values and performance.

        Args:
            account_id: Filter by account ID

        Returns:
            Dictionary with portfolio summary
        """
        try:
            holdings = self.get_holdings(account_id=account_id)

            total_value = Decimal('0')
            total_cost = Decimal('0')
            holdings_data = []

            for holding in holdings:
                current_value = holding.current_value
                cost = holding.total_cost
                gain_loss = holding.gain_loss
                gain_loss_pct = holding.gain_loss_percentage

                total_value += current_value
                total_cost += cost

                holdings_data.append({
                    'stock_id': holding.stock.id,
                    'symbol': holding.stock.symbol,
                    'name': holding.stock.name,
                    'shares': holding.shares,
                    'average_cost': holding.average_cost,
                    'current_price': holding.stock.last_price,
                    'current_value': current_value,
                    'total_cost': cost,
                    'gain_loss': gain_loss,
                    'gain_loss_percentage': gain_loss_pct,
                    'last_updated': holding.stock.last_updated
                })

            total_gain_loss = total_value - total_cost
            total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else Decimal('0')

            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_percentage': total_gain_loss_pct,
                'holdings_count': len(holdings),
                'holdings': holdings_data
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'total_value': Decimal('0'),
                'total_cost': Decimal('0'),
                'total_gain_loss': Decimal('0'),
                'total_gain_loss_percentage': Decimal('0'),
                'holdings_count': 0,
                'holdings': []
            }

    def get_stock_transactions(
        self,
        account_id: Optional[int] = None,
        stock_id: Optional[int] = None,
        transaction_type: Optional[StockTransactionType] = None,
        limit: Optional[int] = None
    ) -> List[StockTransaction]:
        """
        Get stock transactions with optional filtering.

        Args:
            account_id: Filter by account ID
            stock_id: Filter by stock ID
            transaction_type: Filter by transaction type
            limit: Maximum number of results

        Returns:
            List of stock transactions
        """
        query = self.session.query(StockTransaction)

        if account_id is not None:
            query = query.filter(StockTransaction.account_id == account_id) # type: ignore [reportArgumentTypeIssue]

        if stock_id is not None:
            query = query.filter(StockTransaction.stock_id == stock_id) # type: ignore [reportArgumentTypeIssue]

        if transaction_type is not None:
            query = query.filter(StockTransaction.transaction_type == transaction_type) # type: ignore [reportArgumentTypeIssue]

        query = query.order_by(StockTransaction.date.desc(), StockTransaction.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_stock_transaction(self, transaction_id: int) -> Optional[StockTransaction]:
        """
        Get stock transaction by ID.

        Args:
            transaction_id: Stock transaction ID

        Returns:
            Stock transaction instance or None if not found
        """
        return self.session.query(StockTransaction).filter(StockTransaction.id == transaction_id).first()

    def delete_stock_transaction(self, transaction_id: int, update_holding: bool = True) -> bool:
        """
        Delete a stock transaction and optionally update holdings.

        Args:
            transaction_id: Stock transaction ID
            update_holding: Whether to update holdings

        Returns:
            True if deleted successfully, False if not found
        """
        try:
            transaction = self.get_stock_transaction(transaction_id)
            if not transaction:
                return False

            # If updating holdings, reverse the transaction effect
            if update_holding and transaction.transaction_type in [StockTransactionType.BUY, StockTransactionType.SELL]:
                self._reverse_holding_from_transaction(transaction)

            self.session.delete(transaction)
            self.session.commit()

            logger.info(f"Deleted stock transaction {transaction_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting stock transaction {transaction_id}: {e}")
            raise

    def _reverse_holding_from_transaction(self, transaction: StockTransaction) -> None:
        """Reverse the effect of a transaction on holdings."""
        # Find existing holding
        holding = (
            self.session.query(Holding)
            .filter(
                Holding.account_id == transaction.account_id, # type: ignore [reportArgumentTypeIssue]
                Holding.stock_id == transaction.stock_id # type: ignore [reportArgumentTypeIssue]
            )
            .first()
        )

        if not holding:
            return

        if transaction.transaction_type == StockTransactionType.BUY:
            # Reverse a buy transaction by reducing shares
            holding.update_shares(-transaction.shares, transaction.price_per_share) # type: ignore [reportArgumentTypeIssue]

            # Remove holding if no shares left
            if holding.shares <= 0:
                self.session.delete(holding)

        elif transaction.transaction_type == StockTransactionType.SELL:
            # Reverse a sell transaction by adding shares back
            holding.update_shares(transaction.shares, transaction.price_per_share) # type: ignore [reportArgumentTypeIssue]

    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stocks using financial data service.

        Args:
            query: Search query

        Returns:
            List of stock search results
        """
        return self.financial_data_service.search_stocks(query)

    def get_stock_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a stock.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of historical price records
        """
        return self.financial_data_service.get_historical_prices(symbol, start_date, end_date)
