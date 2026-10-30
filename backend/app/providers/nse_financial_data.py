import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from typing import Any

import requests


NSE_HOME_URL = "https://www.nseindia.com"

# Results filed up to Dec-2024 quarter (old SEBI XBRL format).
NSE_LEGACY_RESULTS_URL = (
    "https://www.nseindia.com/api/corporates-financial-results"
    "?index=equities&symbol={symbol}&period=Quarterly"
)

# SEBI "Integrated Filing - Financials", used from the Mar-2025 quarter on.
NSE_INTEGRATED_RESULTS_URL = (
    "https://www.nseindia.com/api/integrated-filing-results"
    "?index=equities&symbol={symbol}"
    "&type=Integrated%20Filing-%20Financials"
)

XBRLI_NS = "{http://www.xbrl.org/2003/instance}"

IST = timezone(timedelta(hours=5, minutes=30))


# Each field maps to XBRL element names (namespace-agnostic), tried in order.
# Banks file in a different format, so their element names come second.
FIELD_ELEMENTS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "RevenueFromOperations",
        "InterestEarned",
    ),
    "other_income": (
        "OtherIncome",
    ),
    "total_income": (
        "Income",
    ),
    "expenses": (
        "Expenses",
    ),
    "finance_costs": (
        "FinanceCosts",
        "InterestExpended",
    ),
    "depreciation": (
        "DepreciationDepletionAndAmortisationExpense",
    ),
    "profit_before_tax": (
        "ProfitBeforeTax",
        "ProfitLossFromOrdinaryActivitiesBeforeTax",
    ),
    "tax": (
        "TaxExpense",
    ),
    "net_profit": (
        "ProfitLossForPeriod",
        "ProfitLossForThePeriod",
    ),
    "net_profit_owners": (
        "ProfitOrLossAttributableToOwnersOfParent",
        "ProfitLossAfterTaxesMinorityInterestAndShareOfProfitLossOfAssociates",
    ),
    "eps_basic": (
        "BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations",
        "BasicEarningsPerShareAfterExtraordinaryItems",
        "BasicEarningsLossPerShareFromContinuingOperations",
    ),
    "eps_diluted": (
        "DilutedEarningsLossPerShareFromContinuingAndDiscontinuedOperations",
        "DilutedEarningsPerShareAfterExtraordinaryItems",
        "DilutedEarningsLossPerShareFromContinuingOperations",
    ),
    "paid_up_capital": (
        "PaidUpValueOfEquityShareCapital",
    ),
    "face_value": (
        "FaceValueOfEquityShareCapital",
    ),
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_nse_date(value: str | None) -> date | None:
    if not value:
        return None

    for pattern in ("%d-%b-%Y", "%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"):
        try:
            return datetime.strptime(value.strip().title(), pattern).date()
        except ValueError:
            continue

    return None


def _parse_nse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    for pattern in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"):
        try:
            return datetime.strptime(
                value.strip(), pattern
            ).replace(tzinfo=IST)
        except ValueError:
            continue

    return None


def _is_xbrl_url(url: str | None) -> bool:
    # Filings without XBRL list the URL as ".../xbrl/-".
    return bool(url) and url.startswith("http") and url.lower().endswith(".xml")


def _quarter_start(period_end: date) -> date:
    """First day of the three-month quarter ending on `period_end`."""
    month = period_end.month - 2
    year = period_end.year

    if month <= 0:
        month += 12
        year -= 1

    return date(year, month, 1)


def parse_results_xbrl(content: bytes) -> dict[str, Any]:
    """
    Extract headline P&L figures for the reporting quarter from an NSE
    results XBRL instance (legacy or integrated filing).

    The reporting quarter is the shortest duration context without any
    dimensions; NSE names it "OneD" in practice.
    """
    root = ET.fromstring(content)

    durations: dict[str, tuple[date, date]] = {}

    for context in root.iter(f"{XBRLI_NS}context"):
        context_id = context.get("id")

        has_dimensions = (
            context.find(f".//{XBRLI_NS}segment") is not None
            or context.find(f".//{XBRLI_NS}scenario") is not None
        )

        start = context.find(f".//{XBRLI_NS}startDate")
        end = context.find(f".//{XBRLI_NS}endDate")

        if (
            context_id
            and not has_dimensions
            and start is not None
            and end is not None
        ):
            durations[context_id] = (
                date.fromisoformat(start.text.strip()),
                date.fromisoformat(end.text.strip()),
            )

    if "OneD" in durations:
        quarter_context = "OneD"
    elif durations:
        latest_end = max(end for _, end in durations.values())

        quarter_context = min(
            (
                context_id
                for context_id, (_, end) in durations.items()
                if end == latest_end
            ),
            key=lambda cid: (durations[cid][1] - durations[cid][0]),
        )
    else:
        # Some 2019-2022 filings reference "OneD" without declaring it.
        quarter_context = "OneD"

    values: dict[str, str] = {}

    for element in root.iter():
        if element.get("contextRef") != quarter_context:
            continue

        name = _local_name(element.tag)

        if name not in values and element.text:
            values[name] = element.text.strip()

    if quarter_context in durations:
        period_start, period_end = durations[quarter_context]
    else:
        try:
            period_end = date.fromisoformat(
                values["DateOfEndOfReportingPeriod"]
            )
        except (KeyError, ValueError):
            raise ValueError("No reporting period found in XBRL.") from None

        if "DateOfStartOfReportingPeriod" in values:
            period_start = date.fromisoformat(
                values["DateOfStartOfReportingPeriod"]
            )
        else:
            period_start = _quarter_start(period_end)

    result: dict[str, Any] = {
        "period_start": period_start,
        "period_end": period_end,
        # NBFCs also report InterestEarned; only banks report InterestExpended.
        "is_bank": "InterestExpended" in values,
    }

    for field, element_names in FIELD_ELEMENTS.items():
        result[field] = None

        for element_name in element_names:
            raw = values.get(element_name)

            if raw is None:
                continue

            try:
                result[field] = float(raw)
            except ValueError:
                continue

            break

    if result["net_profit_owners"] is None:
        result["net_profit_owners"] = result["net_profit"]

    if (
        result["expenses"] is None
        and result["total_income"] is not None
        and result["profit_before_tax"] is not None
    ):
        result["expenses"] = (
            result["total_income"] - result["profit_before_tax"]
        )

    return result


class NSEFinancialResultsProvider:
    """
    Lists and downloads quarterly financial results filed on NSE.
    """

    def __init__(
        self,
        request_delay: float = 0.6,
    ) -> None:
        self.request_delay = request_delay
        self._initialized = False

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                ),
                "Accept": "application/json,text/html,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": (
                    "https://www.nseindia.com/"
                    "companies-listing/corporate-filings-financial-results"
                ),
            }
        )

    def _refresh_session(self) -> None:
        self.session.cookies.clear()
        self.session.get(NSE_HOME_URL, timeout=15).raise_for_status()
        self._initialized = True

    def _get(
        self,
        url: str,
        timeout: int = 30,
        attempts: int = 4,
    ) -> requests.Response:
        """
        GET with retries. NSE throttles sustained scraping by stalling
        requests or expiring cookies, so back off and start a fresh
        session before retrying.
        """
        for attempt in range(attempts):
            try:
                if not self._initialized:
                    self._refresh_session()

                time.sleep(self.request_delay)

                response = self.session.get(url, timeout=timeout)

                if response.status_code in (401, 403, 429) or (
                    response.status_code >= 500
                ):
                    raise requests.HTTPError(
                        f"{response.status_code} for {url}",
                        response=response,
                    )

                response.raise_for_status()

                return response

            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
                status = getattr(exc.response, "status_code", None)

                # A 404 is a real answer, not throttling.
                if status == 404 or attempt == attempts - 1:
                    raise

                wait = 10 * 2**attempt
                print(f"  NSE request failed ({exc}); retrying in {wait}s")
                time.sleep(wait)
                self._initialized = False

        raise RuntimeError("unreachable")

    def list_filings(self, symbol: str) -> list[dict[str, Any]]:
        """
        All quarterly result filings with an XBRL file, newest first.
        """
        symbol = symbol.strip().upper()
        filings: list[dict[str, Any]] = []

        legacy = self._get(
            NSE_LEGACY_RESULTS_URL.format(symbol=symbol)
        ).json()

        for row in legacy:
            xbrl = row.get("xbrl")

            if not _is_xbrl_url(xbrl):
                continue

            filings.append(
                {
                    "period_end": _parse_nse_date(row.get("toDate")),
                    "consolidated": row.get("consolidated") == "Consolidated",
                    "audited": row.get("audited") == "Audited",
                    "filing_date": _parse_nse_datetime(row.get("broadCastDate")),
                    "xbrl_url": xbrl,
                }
            )

        integrated = self._get(
            NSE_INTEGRATED_RESULTS_URL.format(symbol=symbol)
        ).json()

        for row in integrated.get("data", []):
            xbrl = row.get("xbrl")

            if not _is_xbrl_url(xbrl):
                continue

            filings.append(
                {
                    "period_end": _parse_nse_date(row.get("qe_Date")),
                    "consolidated": row.get("consolidated") == "Consolidated",
                    "audited": row.get("audited") == "Audited",
                    "filing_date": _parse_nse_datetime(row.get("broadcast_Date")),
                    "xbrl_url": xbrl,
                }
            )

        filings = [f for f in filings if f["period_end"] is not None]

        filings.sort(
            key=lambda f: (
                f["period_end"],
                f["filing_date"] or datetime.min.replace(tzinfo=IST),
            ),
            reverse=True,
        )

        return filings

    def get_result(self, filing: dict[str, Any]) -> dict[str, Any]:
        content = self._get(filing["xbrl_url"]).content

        result = parse_results_xbrl(content)

        result.update(
            consolidated=filing["consolidated"],
            audited=filing["audited"],
            filing_date=filing["filing_date"],
            source_url=filing["xbrl_url"],
        )

        return result
