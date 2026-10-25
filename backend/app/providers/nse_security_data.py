import io
from typing import Any

import pandas as pd
import requests

from backend.app.providers.company_data import CompanyDataProvider


NSE_EQUITY_URL = (
    "https://nsearchives.nseindia.com/"
    "content/equities/EQUITY_L.csv"
)

NSE_HOME_URL = "https://www.nseindia.com"


class NSESecurityProvider(CompanyDataProvider):
    """
    NSE security master provider.

    Downloads the official NSE equity security list and converts
    it into a standardized structure used by Fin Pro.
    """

    def __init__(self) -> None:
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _download_equity_master(self) -> pd.DataFrame:
        """
        Download the latest official NSE equity security master.
        """

        self.session.get(
            NSE_HOME_URL,
            timeout=15,
        )

        response = self.session.get(
            NSE_EQUITY_URL,
            timeout=30,
        )

        response.raise_for_status()

        dataframe = pd.read_csv(
            io.BytesIO(response.content)
        )

        print("\nNSE columns detected:")
        print(list(dataframe.columns))
        print()

        return dataframe

    @staticmethod
    def _find_column(
        dataframe: pd.DataFrame,
        possible_names: list[str],
    ) -> str | None:
        """
        Find a column using normalized names.

        This protects us from small changes in NSE's
        capitalization, spacing or punctuation.
        """

        normalized_columns = {
            str(column)
            .strip()
            .upper()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", ""): column
            for column in dataframe.columns
        }

        for name in possible_names:
            normalized_name = (
                name
                .strip()
                .upper()
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if normalized_name in normalized_columns:
                return normalized_columns[normalized_name]

        return None

    def get_security_master(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return the complete NSE equity security universe.
        """

        dataframe = self._download_equity_master()

        symbol_column = self._find_column(
            dataframe,
            [
                "SYMBOL",
                "Symbol",
            ],
        )

        company_column = self._find_column(
            dataframe,
            [
                "NAME OF COMPANY",
                "NAMEOFCOMPANY",
                "COMPANY NAME",
                "NAME",
            ],
        )

        series_column = self._find_column(
            dataframe,
            [
                "SERIES",
                "SERIES CODE",
            ],
        )

        isin_column = self._find_column(
            dataframe,
            [
                "ISIN NUMBER",
                "ISIN",
                "ISIN NO",
            ],
        )

        listing_date_column = self._find_column(
            dataframe,
            [
                "DATE OF LISTING",
                "LISTING DATE",
            ],
        )

        paid_up_column = self._find_column(
            dataframe,
            [
                "PAID UP VALUE",
                "PAIDUP VALUE",
                "PAID UP",
            ],
        )

        market_lot_column = self._find_column(
            dataframe,
            [
                "MARKET LOT",
                "MARKETLOT",
            ],
        )

        face_value_column = self._find_column(
            dataframe,
            [
                "FACE VALUE",
                "FACEVALUE",
            ],
        )

        missing = []

        if symbol_column is None:
            missing.append("SYMBOL")

        if company_column is None:
            missing.append("COMPANY NAME")

        if series_column is None:
            missing.append("SERIES")

        if isin_column is None:
            missing.append("ISIN")

        if missing:
            raise ValueError(
                "Unable to identify required NSE columns: "
                f"{missing}\n"
                f"Available columns: {list(dataframe.columns)}"
            )

        securities: list[dict[str, Any]] = []

        for _, row in dataframe.iterrows():
            symbol = str(
                row[symbol_column]
            ).strip().upper()

            if not symbol:
                continue

            security = {
                "name": str(
                    row[company_column]
                ).strip(),

                "ticker": symbol,

                "exchange": "NSE",

                "series": str(
                    row[series_column]
                ).strip(),

                "isin": str(
                    row[isin_column]
                ).strip(),

                "date_of_listing": (
                    str(row[listing_date_column]).strip()
                    if listing_date_column
                    else None
                ),

                "paid_up_value": (
                    row[paid_up_column]
                    if paid_up_column
                    else None
                ),

                "market_lot": (
                    row[market_lot_column]
                    if market_lot_column
                    else None
                ),

                "face_value": (
                    row[face_value_column]
                    if face_value_column
                    else None
                ),

                "security_type": "EQUITY",

                "status": "ACTIVE",
            }

            securities.append(security)

        return securities

    def get_company_profile(
        self,
        ticker: str,
    ) -> dict[str, Any]:
        ticker = ticker.strip().upper()

        securities = self.get_security_master()

        for security in securities:
            if security["ticker"] == ticker:
                return security

        raise ValueError(
            f"NSE security not found: {ticker}"
        )

    def search_companies(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        query = query.strip().lower()

        if not query:
            return []

        securities = self.get_security_master()

        results = []

        for security in securities:
            if (
                query in security["ticker"].lower()
                or query in security["name"].lower()
            ):
                results.append(security)

        return results