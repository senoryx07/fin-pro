from abc import ABC, abstractmethod
from typing import Any


class FinancialDataProvider(ABC):
    """
    Base interface for financial statement and company
    financial data providers.
    """

    @abstractmethod
    def get_income_statement(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Return historical income statement data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_balance_sheet(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Return historical balance sheet data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_cash_flow(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Return historical cash flow data.
        """
        raise NotImplementedError

    @abstractmethod
    def get_shareholding_pattern(
        self,
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Return historical shareholding information.
        """
        raise NotImplementedError