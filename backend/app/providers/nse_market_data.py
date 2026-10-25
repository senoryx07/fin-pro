import io
import zipfile
from datetime import date, datetime
from typing import Any

import pandas as pd
import requests


NSE_HOME_URL = "https://www.nseindia.com"

NSE_BHAVCOPY_URL = (
    "https://nsearchives.nseindia.com/"
    "content/cm/BhavCopy_NSE_CM_0_0_0_"
    "{date}_F_0000.csv.zip"
)


class NSEMarketDataProvider:
    """
    Retrieves daily NSE cash-market bhavcopy data.

    NSE's current CM daily format is the
    UDiFF Common Bhavcopy Final ZIP.
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

    def _initialize_session(self) -> None:
        """
        Establish an NSE session before requesting archives.
        """

        response = self.session.get(
            NSE_HOME_URL,
            timeout=15,
        )

        response.raise_for_status()

    def _build_url(
        self,
        trade_date: date,
    ) -> str:
        """
        Build the official NSE bhavcopy archive URL.
        """

        date_code = trade_date.strftime(
            "%Y%m%d"
        )

        return NSE_BHAVCOPY_URL.format(
            date=date_code
        )

    def _download_bhavcopy(
        self,
        trade_date: date,
    ) -> bytes:
        """
        Download the official NSE daily bhavcopy ZIP.
        """

        self._initialize_session()

        url = self._build_url(
            trade_date
        )

        response = self.session.get(
            url,
            timeout=30,
        )

        if response.status_code == 404:
            raise FileNotFoundError(
                "NSE bhavcopy was not found for "
                f"{trade_date.isoformat()}."
            )

        response.raise_for_status()

        return response.content

    @staticmethod
    def _read_zip(
        content: bytes,
    ) -> pd.DataFrame:
        """
        Extract and read the CSV contained in
        the NSE bhavcopy ZIP.
        """

        with zipfile.ZipFile(
            io.BytesIO(content)
        ) as archive:

            csv_files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv")
            ]

            if not csv_files:
                raise ValueError(
                    "No CSV file found inside "
                    "NSE bhavcopy ZIP."
                )

            with archive.open(
                csv_files[0]
            ) as csv_file:

                dataframe = pd.read_csv(
                    csv_file
                )

        return dataframe

    @staticmethod
    def _find_column(
        dataframe: pd.DataFrame,
        candidates: list[str],
    ) -> str | None:
        """
        Find a dataframe column while tolerating
        differences in capitalization and spacing.
        """

        normalized = {
            str(column)
            .strip()
            .upper()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", ""): column
            for column in dataframe.columns
        }

        for candidate in candidates:
            key = (
                candidate
                .strip()
                .upper()
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if key in normalized:
                return normalized[key]

        return None

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date:
        """
        Convert NSE date values into Python dates.
        """

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value).strip()

        formats = [
            "%d-%b-%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()
            except ValueError:
                continue

        raise ValueError(
            f"Unable to parse NSE trade date: {value}"
        )

    @staticmethod
    def _clean_number(
        value: Any,
    ) -> float | None:
        """
        Convert numeric NSE values into floats.
        """

        if value is None:
            return None

        text = str(value).strip()

        if text.upper() in {
            "",
            "NA",
            "N/A",
            "NULL",
            "NAN",
            "-",
        }:
            return None

        try:
            return float(
                text.replace(",", "")
            )
        except ValueError:
            return None

    def get_daily_prices(
        self,
        trade_date: date,
    ) -> list[dict[str, Any]]:
        """
        Download and normalize one NSE trading day's
        cash-market price data.
        """

        content = self._download_bhavcopy(
            trade_date
        )

        dataframe = self._read_zip(
            content
        )

        print("\nNSE market-data columns detected:")
        print(list(dataframe.columns))
        print()

        symbol_column = self._find_column(
            dataframe,
            [
                "TckrSymb",
                "Symbol",
                "SYMBOL",
            ],
        )

        series_column = self._find_column(
            dataframe,
            [
                "SctySrs",
                "Series",
                "SERIES",
            ],
        )

        trade_date_column = self._find_column(
            dataframe,
            [
                "TradDt",
                "Trade Date",
                "TIMESTAMP",
                "DATE",
            ],
        )

        open_column = self._find_column(
            dataframe,
            [
                "OpnPric",
                "Open Price",
                "OPEN",
            ],
        )

        high_column = self._find_column(
            dataframe,
            [
                "HghPric",
                "High Price",
                "HIGH",
            ],
        )

        low_column = self._find_column(
            dataframe,
            [
                "LwPric",
                "Low Price",
                "LOW",
            ],
        )

        close_column = self._find_column(
            dataframe,
            [
                "ClsPric",
                "Close Price",
                "CLOSE",
            ],
        )

        previous_close_column = self._find_column(
            dataframe,
            [
                "PrvsClsgPric",
                "Previous Close",
                "PREVCLOSE",
            ],
        )

        last_price_column = self._find_column(
            dataframe,
            [
                "LastPric",
                "Last Price",
                "LTP",
            ],
        )

        volume_column = self._find_column(
            dataframe,
            [
                "TtlTradgVol",
                "Total Traded Quantity",
                "TOTTRDQTY",
                "Volume",
            ],
        )

        traded_value_column = self._find_column(
            dataframe,
            [
                "TtlTrfVal",
                "Turnover",
                "Turnover (₹ Lakhs)",
                "Traded Value",
            ],
        )

        required_columns = {
            "symbol": symbol_column,
            "trade_date": trade_date_column,
            "open": open_column,
            "high": high_column,
            "low": low_column,
            "close": close_column,
        }

        missing = [
            name
            for name, column in required_columns.items()
            if column is None
        ]

        if missing:
            raise ValueError(
                "Unable to identify required NSE "
                "market-data columns: "
                f"{missing}\n"
                f"Available columns: "
                f"{list(dataframe.columns)}"
            )

        records: list[dict[str, Any]] = []

        for _, row in dataframe.iterrows():

            symbol = str(
                row[symbol_column]
            ).strip().upper()

            if not symbol:
                continue

            series = (
                str(row[series_column]).strip().upper()
                if series_column
                else None
            )

            # Fin Pro currently focuses on the
            # standard NSE equity universe.
            #
            # Keep the main EQ series and also retain
            # other equity-series records when NSE
            # supplies them. The Security table is the
            # source of truth for whether the ticker
            # exists in our universe.

            records.append(
                {
                    "ticker": symbol,
                    "series": series,
                    "trade_date": self._parse_date(
                        row[trade_date_column]
                    ),
                    "open": self._clean_number(
                        row[open_column]
                    ),
                    "high": self._clean_number(
                        row[high_column]
                    ),
                    "low": self._clean_number(
                        row[low_column]
                    ),
                    "close": self._clean_number(
                        row[close_column]
                    ),
                    "previous_close": (
                        self._clean_number(
                            row[previous_close_column]
                        )
                        if previous_close_column
                        else None
                    ),
                    "last_price": (
                        self._clean_number(
                            row[last_price_column]
                        )
                        if last_price_column
                        else None
                    ),
                    "volume": (
                        int(
                            self._clean_number(
                                row[volume_column]
                            )
                        )
                        if volume_column
                        and self._clean_number(
                            row[volume_column]
                        )
                        is not None
                        else None
                    ),
                    "traded_value": (
                        self._clean_number(
                            row[traded_value_column]
                        )
                        if traded_value_column
                        else None
                    ),
                    "source": "NSE",
                }
            )

        return records