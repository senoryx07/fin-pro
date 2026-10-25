from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class MarketDataProvider(ABC):
    """
    Base interface for market data providers.

    A provider is responsible only for retrieving market data.
    It should not perform financial analysis or valuation.
    """

    @abstractmethod
    def get_quote(self, ticker: str) -> dict[str, Any]:
        """
        Return the latest available market quote.
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Return historical OHLCV data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_corporate_actions(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Return corporate actions such as splits,
        bonuses, dividends and rights issues.
        """
        raise NotImplementedError