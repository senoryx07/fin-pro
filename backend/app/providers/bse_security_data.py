import io
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.providers.company_data import CompanyDataProvider


class BSESecurityProvider(CompanyDataProvider):
    """
    BSE security master provider.

    The provider is intentionally separated from the ingestion layer.
    This allows Fin Pro to consume an official BSE security-master file
    without coupling the rest of the application to BSE's file format.
    """

    def __init__(
        self,
        file_path: str | None = None,
    ) -> None:
        self.file_path = file_path

    def _load_file(self) -> pd.DataFrame:
        if not self.file_path:
            raise ValueError(
                "No BSE security master file supplied. "
                "Provide the official BSE_EQ_SCRIP_DDMMYYYY.csv "
                "file path."
            )

        path = Path(self.file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"BSE security master file not found: {path}"
            )

        dataframe = pd.read_csv(
            path,
            dtype=str,
        )

        dataframe.columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        return dataframe

    @staticmethod
    def _find_column(
        dataframe: pd.DataFrame,
        possible_names: list[str],
    ) -> str | None:
        normalized_columns = {
            (
                str(column)
                .strip()
                .upper()
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            ): column
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
                return normalized_columns[
                    normalized_name
                ]

        return None

    def get_security_master(
        self,
    ) -> list[dict[str, Any]]:
        dataframe = self._load_file()

        code_column = self._find_column(
            dataframe,
            [
                "SCRIP CODE",
                "SCRIPCODE",
                "SECURITY CODE",
            ],
        )

        symbol_column = self._find_column(
            dataframe,
            [
                "INSTRUMENT CODE",
                "SECURITY ID",
                "SECURITYID",
                "SYMBOL",
            ],
        )

        name_column = self._find_column(
            dataframe,
            [
                "SCRIP NAME",
                "SCRIPNAME",
                "SECURITY NAME",
            ],
        )

        isin_column = self._find_column(
            dataframe,
            [
                "ISIN CODE",
                "ISINCODE",
                "ISIN",
            ],
        )

        group_column = self._find_column(
            dataframe,
            [
                "GROUP NAME",
                "GROUPNAME",
            ],
        )

        security_type_column = self._find_column(
            dataframe,
            [
                "SECURITY TYPE FLAG",
                "SECURITYTYPEFLAG",
                "SECURITY TYPE",
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

        if code_column is None:
            missing.append("SCRIP CODE")

        if name_column is None:
            missing.append("SCRIP NAME")

        if isin_column is None:
            missing.append("ISIN")

        if security_type_column is None:
            missing.append("SECURITY TYPE")

        if missing:
            raise ValueError(
                "Unable to identify required BSE columns: "
                f"{missing}\n"
                f"Available columns: "
                f"{list(dataframe.columns)}"
            )

        securities: list[dict[str, Any]] = []

        for _, row in dataframe.iterrows():
            security_type = str(
                row[security_type_column]
            ).strip().upper()

            # We are building the listed-equity universe first.
            if security_type != "EQ":
                continue

            scrip_code = str(
                row[code_column]
            ).strip()

            if not scrip_code:
                continue

            symbol = (
                str(row[symbol_column]).strip().upper()
                if symbol_column
                else None
            )

            name = str(
                row[name_column]
            ).strip()

            isin = str(
                row[isin_column]
            ).strip().upper()

            securities.append(
                {
                    "name": name,
                    "ticker": symbol,
                    "exchange": "BSE",
                    "exchange_code": scrip_code,
                    "isin": isin,
                    "series": (
                        str(row[group_column]).strip()
                        if group_column
                        else None
                    ),
                    "security_type": "EQUITY",
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
                    "status": "ACTIVE",
                }
            )

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
            f"BSE security not found: {ticker}"
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
            symbol = security["ticker"] or ""

            if (
                query in symbol.lower()
                or query in security["name"].lower()
                or query in security["exchange_code"].lower()
            ):
                results.append(security)

        return results