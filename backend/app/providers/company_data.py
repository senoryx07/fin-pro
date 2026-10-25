from abc import ABC, abstractmethod
from typing import Any


class CompanyDataProvider(ABC):
    """
    Base interface for company reference information.
    """

    @abstractmethod
    def get_company_profile(
        self,
        ticker: str,
    ) -> dict[str, Any]:
        """
        Return standardized company profile information.
        """
        raise NotImplementedError

    @abstractmethod
    def search_companies(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """
        Search for companies by name, ticker or identifier.
        """
        raise NotImplementedError