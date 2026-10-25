from datetime import date
from typing import Any

from backend.app.providers.market_data import MarketDataProvider


class MockMarketDataProvider(MarketDataProvider):
    """
    Temporary provider used to test Fin Pro's data architecture.

    This will later be replaced by a real market-data provider.
    """

    def get_quote(self, ticker: str) -> dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "price": 1250.00,
            "change": 12.50,
            "change_percent": 1.01,
            "currency": "INR",
        }

    def get_historical_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        return [
            {
                "date": "2026-09-25",
                "open": 1235.00,
                "high": 1260.00,
                "low": 1228.00,
                "close": 1250.00,
                "volume": 1000000,
            }
        ]

    def get_corporate_actions(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        return []