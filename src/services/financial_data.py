"""
Financial data service for fetching stock prices and market data.

This module provides a flexible abstraction layer for financial data APIs,
starting with yfinance and Stockdex as fallback options.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any

import requests
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class FinancialDataProvider(ABC):
    """Abstract base class for financial data providers."""
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """Get current stock price for a symbol."""
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information."""
        pass
    
    @abstractmethod
    def get_historical_prices(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get historical price data."""
        pass
    
    @abstractmethod
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """Search for stocks by name or symbol."""
        pass


class YFinanceProvider(FinancialDataProvider):
    """Financial data provider using yfinance library."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize YFinance provider.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current stock price using yfinance.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Current stock price or None if not found
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if price is not None:
                return Decimal(str(price))
            
            logger.warning(f"No price found for symbol {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed stock information using yfinance.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with stock information or None if not found
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            return {
                'symbol': symbol.upper(),
                'name': info.get('longName', ''),
                'exchange': info.get('exchange', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'currency': info.get('currency', 'USD'),
                'description': info.get('longBusinessSummary', ''),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
            }
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return None
    
    def get_historical_prices(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data using yfinance.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of historical price records
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return []
            
            records = []
            for date_idx, row in hist.iterrows():
                records.append({
                    'date': date_idx.date(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stocks (limited functionality in yfinance).
        
        Args:
            query: Search query
            
        Returns:
            List of stock search results
        """
        # yfinance doesn't have a built-in search function
        # This is a placeholder for future implementation
        logger.warning("Stock search not implemented for YFinance provider")
        return []


class StockdexProvider(FinancialDataProvider):
    """Financial data provider using Stockdex API."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        Initialize Stockdex provider.
        
        Args:
            api_key: Stockdex API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.stockdx.com/v1"
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make API request to Stockdx."""
        if not self.api_key:
            logger.warning("Stockdx API key not provided")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = self.session.get(
                url, 
                headers=headers, 
                params=params or {}, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Stockdx API request failed: {e}")
            return None
    
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """Get current stock price using Stockdx API."""
        data = self._make_request(f"stocks/{symbol}/quote")
        
        if data and 'price' in data:
            return Decimal(str(data['price']))
        
        return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information using Stockdx API."""
        data = self._make_request(f"stocks/{symbol}")
        
        if data:
            return {
                'symbol': symbol.upper(),
                'name': data.get('name', ''),
                'exchange': data.get('exchange', ''),
                'sector': data.get('sector', ''),
                'industry': data.get('industry', ''),
                'currency': data.get('currency', 'USD'),
                'description': data.get('description', ''),
            }
        
        return None
    
    def get_historical_prices(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get historical price data using Stockdx API."""
        params = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        data = self._make_request(f"stocks/{symbol}/history", params)
        
        if data and 'prices' in data:
            return data['prices']
        
        return []
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """Search for stocks using Stockdx API."""
        params = {'q': query}
        data = self._make_request("stocks/search", params)
        
        if data and 'results' in data:
            return data['results']
        
        return []


class FinancialDataService:
    """
    Main financial data service that manages multiple providers.

    This service provides a unified interface for financial data and handles
    fallback between different providers.
    """

    def __init__(self, yfinance_timeout: int = 10, stockdx_api_key: Optional[str] = None):
        """
        Initialize the financial data service.

        Args:
            yfinance_timeout: Timeout for yfinance requests
            stockdx_api_key: API key for Stockdx service
        """
        self.providers = [
            YFinanceProvider(timeout=yfinance_timeout),
        ]

        # Add Stockdx provider if API key is available
        if stockdx_api_key:
            self.providers.append(StockdexProvider(api_key=stockdx_api_key))

    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current stock price with fallback between providers.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Current stock price or None if not found
        """
        for provider in self.providers:
            try:
                price = provider.get_stock_price(symbol)
                if price is not None:
                    logger.info(f"Got price for {symbol} from {provider.__class__.__name__}")
                    return price
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue

        logger.error(f"All providers failed to get price for {symbol}")
        return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed stock information with fallback between providers.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with stock information or None if not found
        """
        for provider in self.providers:
            try:
                info = provider.get_stock_info(symbol)
                if info is not None:
                    logger.info(f"Got info for {symbol} from {provider.__class__.__name__}")
                    return info
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue

        logger.error(f"All providers failed to get info for {symbol}")
        return None

    def get_historical_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data with fallback between providers.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of historical price records
        """
        for provider in self.providers:
            try:
                data = provider.get_historical_prices(symbol, start_date, end_date)
                if data:
                    logger.info(f"Got historical data for {symbol} from {provider.__class__.__name__}")
                    return data
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue

        logger.error(f"All providers failed to get historical data for {symbol}")
        return []

    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        Search for stocks with fallback between providers.

        Args:
            query: Search query

        Returns:
            List of stock search results
        """
        for provider in self.providers:
            try:
                results = provider.search_stocks(query)
                if results:
                    logger.info(f"Got search results for '{query}' from {provider.__class__.__name__}")
                    return results
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for search '{query}': {e}")
                continue

        logger.warning(f"All providers failed to search for '{query}'")
        return []

    def update_stock_prices(self, symbols: List[str]) -> Dict[str, Optional[Decimal]]:
        """
        Update prices for multiple stocks.

        Args:
            symbols: List of stock symbols to update

        Returns:
            Dictionary mapping symbols to their prices
        """
        results = {}

        for symbol in symbols:
            price = self.get_stock_price(symbol)
            results[symbol] = price

            if price is not None:
                logger.info(f"Updated price for {symbol}: ${price}")
            else:
                logger.warning(f"Failed to update price for {symbol}")

        return results
