"""
Unit tests for the Stock Service.

This module tests the StockService class functionality including
stock management, holdings, and portfolio analytics.
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, patch

from src.models import StockTransactionType
from src.services import StockService, FinancialDataService


class TestStockService:
    """Test cases for StockService."""
    
    @pytest.fixture(scope="function")
    def mock_financial_service(self, mock_stock_data):
        """Create a mock financial data service."""
        mock_service = Mock(spec=FinancialDataService)
        mock_service.get_stock_price.return_value = Decimal('150.00')
        mock_service.get_stock_info.return_value = mock_stock_data
        mock_service.get_historical_prices.return_value = []
        mock_service.search_stocks.return_value = []

        return mock_service
    
    def test_create_stock(self, db_session, mock_financial_service):
        """Test creating a new stock."""
        service = StockService(db_session, mock_financial_service)

        stock = service.create_stock(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            currency="USD",
            description="Apple Inc. description",
            fetch_info=False
        )

        assert stock.id is not None
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.exchange == "NASDAQ"
        assert stock.sector == "Technology"
        assert stock.industry == "Consumer Electronics"
        assert stock.currency == "USD"
        assert stock.description == "Apple Inc. description"
    
    def test_create_stock_with_api_fetch(self, db_session, mock_financial_service):
        """Test creating a stock with API data fetch."""
        service = StockService(db_session, mock_financial_service)

        stock = service.create_stock(
            symbol="AAPL",
            name="Apple Inc.",
            fetch_info=True
        )

        assert stock.id is not None
        assert stock.symbol == "AAPL"
        assert stock.last_price == Decimal('150.00')
        assert stock.last_updated is not None

        # Verify API was called
        mock_financial_service.get_stock_info.assert_called_once_with("AAPL")
        mock_financial_service.get_stock_price.assert_called_once_with("AAPL")
    
    def test_create_stock_duplicate(self, db_session, sample_stock, mock_financial_service):
        """Test creating a stock that already exists."""
        service = StockService(db_session, mock_financial_service)
        
        # Try to create the same stock again
        duplicate_stock = service.create_stock(
            symbol=sample_stock.symbol,
            name="Different Name",
            fetch_info=False
        )
        
        # Should return the existing stock
        assert duplicate_stock.id == sample_stock.id
        assert duplicate_stock.name == sample_stock.name  # Original name preserved
    
    def test_get_stock(self, db_session, sample_stock):
        """Test retrieving a stock by ID."""
        service = StockService(db_session)
        
        retrieved_stock = service.get_stock(sample_stock.id)
        
        assert retrieved_stock is not None
        assert retrieved_stock.id == sample_stock.id
        assert retrieved_stock.symbol == sample_stock.symbol
    
    def test_get_stock_not_found(self, db_session):
        """Test retrieving a non-existent stock."""
        service = StockService(db_session)
        
        stock = service.get_stock(99999)
        
        assert stock is None
    
    def test_get_stock_by_symbol(self, db_session, sample_stock):
        """Test retrieving a stock by symbol."""
        service = StockService(db_session)
        
        retrieved_stock = service.get_stock_by_symbol(sample_stock.symbol)
        
        assert retrieved_stock is not None
        assert retrieved_stock.id == sample_stock.id
        assert retrieved_stock.symbol == sample_stock.symbol
    
    def test_get_stock_by_symbol_case_insensitive(self, db_session, sample_stock):
        """Test retrieving a stock by symbol (case insensitive)."""
        service = StockService(db_session)
        
        retrieved_stock = service.get_stock_by_symbol(sample_stock.symbol.lower())
        
        assert retrieved_stock is not None
        assert retrieved_stock.symbol == sample_stock.symbol
    
    def test_get_stock_by_symbol_not_found(self, db_session):
        """Test retrieving a non-existent stock by symbol."""
        service = StockService(db_session)
        
        stock = service.get_stock_by_symbol("NONEXISTENT")
        
        assert stock is None
    
    def test_get_stocks(self, db_session):
        """Test retrieving all stocks."""
        service = StockService(db_session)

        # Create multiple stocks
        stocks_data = [
            ("AAPL", "Apple Inc."),
            ("GOOGL", "Alphabet Inc."),
            ("MSFT", "Microsoft Corporation")
        ]

        for symbol, name in stocks_data:
            service.create_stock(symbol=symbol, name=name, fetch_info=False)

        stocks = service.get_stocks()

        assert len(stocks) == 3
        # Should be ordered by symbol
        symbols = [stock.symbol for stock in stocks]
        assert symbols == sorted(symbols)
    
    def test_get_stocks_with_pagination(self, db_session):
        """Test retrieving stocks with pagination."""
        service = StockService(db_session)

        # Create multiple stocks
        for i in range(5):
            service.create_stock(symbol=f"TEST{i}", name=f"Test Stock {i}", fetch_info=False)

        # Get first 3 stocks
        page1 = service.get_stocks(limit=3, offset=0)
        assert len(page1) == 3

        # Get next 2 stocks
        page2 = service.get_stocks(limit=3, offset=3)
        assert len(page2) == 2
    
    def test_update_stock_price(self, db_session, sample_stock, mock_financial_service):
        """Test updating stock price."""
        service = StockService(db_session, mock_financial_service)
        
        updated_stock = service.update_stock_price(sample_stock.id)
        
        assert updated_stock is not None
        assert updated_stock.last_price == Decimal('150.00')
        assert updated_stock.last_updated is not None
        
        mock_financial_service.get_stock_price.assert_called_once_with(sample_stock.symbol)
    
    def test_update_stock_price_not_found(self, db_session, mock_financial_service):
        """Test updating price for non-existent stock."""
        service = StockService(db_session, mock_financial_service)
        
        result = service.update_stock_price(99999)
        
        assert result is None
    
    def test_update_all_stock_prices(self, db_session, mock_financial_service):
        """Test updating prices for all stocks."""
        service = StockService(db_session, mock_financial_service)

        # Create multiple stocks
        stocks = []
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            stock = service.create_stock(symbol=symbol, name=f"{symbol} Inc.", fetch_info=False)
            stocks.append(stock)

        # Reset mock to clear creation calls
        mock_financial_service.reset_mock()

        results = service.update_all_stock_prices()

        assert len(results) == 3
        assert all(success for success in results.values())
        # Should be called once for each stock during update
        assert mock_financial_service.get_stock_price.call_count == 3
    
    def test_create_holding(self, db_session, sample_brokerage_account, sample_stock):
        """Test creating a stock holding."""
        service = StockService(db_session)
        
        holding = service.create_holding(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            shares=Decimal('10.0'),
            average_cost=Decimal('140.00'),
            purchase_date=date.today(),
            notes="Test holding"
        )
        
        assert holding.id is not None
        assert holding.account_id == sample_brokerage_account.id
        assert holding.stock_id == sample_stock.id
        assert holding.shares == Decimal('10.0')
        assert holding.average_cost == Decimal('140.00')
        assert holding.purchase_date == date.today()
        assert holding.notes == "Test holding"
    
    def test_get_holding(self, db_session, sample_holding):
        """Test retrieving a holding by ID."""
        service = StockService(db_session)
        
        retrieved_holding = service.get_holding(sample_holding.id)
        
        assert retrieved_holding is not None
        assert retrieved_holding.id == sample_holding.id
        assert retrieved_holding.shares == sample_holding.shares
    
    def test_get_holding_not_found(self, db_session):
        """Test retrieving a non-existent holding."""
        service = StockService(db_session)
        
        holding = service.get_holding(99999)
        
        assert holding is None
    
    def test_get_holdings_by_account(self, db_session, sample_brokerage_account, sample_holding):
        """Test retrieving holdings by account."""
        service = StockService(db_session)
        
        holdings = service.get_holdings(account_id=sample_brokerage_account.id)
        
        assert len(holdings) == 1
        assert holdings[0].id == sample_holding.id
    
    def test_get_holdings_by_stock(self, db_session, sample_stock, sample_holding):
        """Test retrieving holdings by stock."""
        service = StockService(db_session)
        
        holdings = service.get_holdings(stock_id=sample_stock.id)
        
        assert len(holdings) == 1
        assert holdings[0].id == sample_holding.id
    
    def test_create_stock_transaction_buy(self, db_session, sample_brokerage_account, sample_stock):
        """Test creating a buy stock transaction."""
        service = StockService(db_session)
        
        transaction = service.create_stock_transaction(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=Decimal('5.0'),
            price_per_share=Decimal('145.00'),
            transaction_date=date.today(),
            fees=Decimal('9.99'),
            notes="Test buy transaction",
            update_holding=False  # Don't update holding for this test
        )
        
        assert transaction.id is not None
        assert transaction.account_id == sample_brokerage_account.id
        assert transaction.stock_id == sample_stock.id
        assert transaction.transaction_type == StockTransactionType.BUY
        assert transaction.shares == Decimal('5.0')
        assert transaction.price_per_share == Decimal('145.00')
        assert transaction.fees == Decimal('9.99')
        assert transaction.total_amount == Decimal('734.99')  # (5 * 145) + 9.99
    
    def test_create_stock_transaction_with_holding_update(self, db_session, sample_brokerage_account, sample_stock):
        """Test creating a stock transaction that updates holdings."""
        service = StockService(db_session)
        
        # Create buy transaction
        transaction = service.create_stock_transaction(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id,
            transaction_type=StockTransactionType.BUY,
            shares=Decimal('10.0'),
            price_per_share=Decimal('140.00'),
            transaction_date=date.today(),
            update_holding=True
        )
        
        assert transaction.id is not None
        
        # Check that holding was created
        holdings = service.get_holdings(
            account_id=sample_brokerage_account.id,
            stock_id=sample_stock.id
        )
        assert len(holdings) == 1
        assert holdings[0].shares == Decimal('10.0')
        assert holdings[0].average_cost == Decimal('140.00')
    
    def test_get_portfolio_summary(self, db_session, sample_holding):
        """Test getting portfolio summary."""
        service = StockService(db_session)
        
        summary = service.get_portfolio_summary()
        
        assert 'total_value' in summary
        assert 'total_cost' in summary
        assert 'total_gain_loss' in summary
        assert 'total_gain_loss_percentage' in summary
        assert 'holdings_count' in summary
        assert 'holdings' in summary
        
        assert summary['holdings_count'] == 1
        assert len(summary['holdings']) == 1
        
        # Check calculations (holding: 10 shares at $140 avg cost, current price $150)
        expected_cost = Decimal('1400.00')  # 10 * 140
        expected_value = Decimal('1500.00')  # 10 * 150
        expected_gain = Decimal('100.00')  # 1500 - 1400
        
        assert summary['total_cost'] == expected_cost
        assert summary['total_value'] == expected_value
        assert summary['total_gain_loss'] == expected_gain
    
    def test_get_stock_transactions(self, db_session, sample_stock_transaction):
        """Test retrieving stock transactions."""
        service = StockService(db_session)
        
        transactions = service.get_stock_transactions()
        
        assert len(transactions) == 1
        assert transactions[0].id == sample_stock_transaction.id
    
    def test_get_stock_transactions_filtered(self, db_session, sample_brokerage_account, sample_stock_transaction):
        """Test retrieving stock transactions with filters."""
        service = StockService(db_session)
        
        # Filter by account
        transactions = service.get_stock_transactions(account_id=sample_brokerage_account.id)
        assert len(transactions) == 1
        
        # Filter by transaction type
        transactions = service.get_stock_transactions(transaction_type=StockTransactionType.BUY)
        assert len(transactions) == 1
        
        # Filter by non-matching type
        transactions = service.get_stock_transactions(transaction_type=StockTransactionType.SELL)
        assert len(transactions) == 0
