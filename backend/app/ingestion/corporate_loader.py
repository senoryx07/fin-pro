"""
Load announcements, corporate actions, board meetings and shareholding
from NSE for the most-traded stocks.

    python -m backend.app.ingestion.corporate_loader --top 500
    python -m backend.app.ingestion.corporate_loader --tickers TCS INFY
"""

import argparse
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, select

from backend.app.database.database import create_db_and_tables, engine
from backend.app.ingestion.financial_loader import top_tickers_by_traded_value
from backend.app.models.corporate import CorporateInfo
from backend.app.models.security import Security
from backend.app.providers.nse_financial_data import NSEFinancialResultsProvider


SUMMARY_URL = (
    "https://www.nseindia.com/api/top-corp-info"
    "?symbol={symbol}&market=equities"
)

ANNOUNCEMENTS_URL = (
    "https://www.nseindia.com/api/corporate-announcements"
    "?index=equities&symbol={symbol}&from_date={start}&to_date={end}"
)

ANNOUNCEMENT_DAYS = 120
MAX_ANNOUNCEMENTS = 30
MAX_TEXT = 400

# Re-fetch a company at most this often.
REFRESH_AFTER = timedelta(hours=20)


def _parse_date(value: str | None, *patterns: str) -> str | None:
    if not value:
        return None

    for pattern in patterns:
        try:
            return datetime.strptime(value.strip(), pattern).date().isoformat()
        except ValueError:
            continue

    return None


def _percent(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def unique_meetings(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    NSE lists each meeting twice (intimation and agenda); keep the shorter,
    more readable description per date.
    """
    by_date: dict[str, dict[str, Any]] = {}

    for meeting in meetings:
        if not meeting["date"]:
            continue

        current = by_date.get(meeting["date"])

        if current is None or len(meeting["purpose"]) < len(current["purpose"]):
            by_date[meeting["date"]] = meeting

    return sorted(by_date.values(), key=lambda m: m["date"], reverse=True)


def normalize(
    summary: dict[str, Any],
    announcements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Keep only what the site shows, in a compact shape."""
    shareholding = []

    for period, rows in (
        summary.get("shareholdings_patterns", {}).get("data", {}) or {}
    ).items():
        values = {k: v for row in rows for k, v in row.items()}

        shareholding.append(
            {
                "date": _parse_date(period, "%d-%b-%Y"),
                "promoter": _percent(values.get("Promoter & Promoter Group")),
                "public": _percent(values.get("Public")),
                "employee_trusts": _percent(
                    values.get("Shares held by Employee Trusts")
                ),
            }
        )

    shareholding = sorted(
        (s for s in shareholding if s["date"]),
        key=lambda s: s["date"],
    )

    actions = [
        {
            "ex_date": _parse_date(a.get("exdate"), "%d-%b-%Y"),
            "purpose": (a.get("purpose") or "").strip(),
        }
        for a in summary.get("corporate_actions", {}).get("data", []) or []
    ]

    meetings = [
        {
            "date": _parse_date(m.get("meetingdate"), "%d-%b-%Y"),
            "purpose": (m.get("purpose") or "").strip(),
        }
        for m in summary.get("borad_meeting", {}).get("data", []) or []
    ]

    items = []

    for a in announcements[:MAX_ANNOUNCEMENTS]:
        text = " ".join((a.get("attchmntText") or "").split())

        if len(text) > MAX_TEXT:
            text = text[: MAX_TEXT - 1].rsplit(" ", 1)[0] + "…"

        url = a.get("attchmntFile") or None

        items.append(
            {
                "date": _parse_date(a.get("an_dt"), "%d-%b-%Y %H:%M:%S"),
                "subject": (a.get("desc") or "").strip(),
                "text": text,
                "url": url if url and url.startswith("http") else None,
            }
        )

    return {
        "announcements": items,
        "actions": [a for a in actions if a["ex_date"]],
        "meetings": unique_meetings(meetings)[:4],
        "shareholding": shareholding,
    }


def load_corporate_info(
    provider: NSEFinancialResultsProvider,
    security: Security,
) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=ANNOUNCEMENT_DAYS)

    summary = provider._get(
        SUMMARY_URL.format(symbol=security.ticker)
    ).json()

    announcements = provider._get(
        ANNOUNCEMENTS_URL.format(
            symbol=security.ticker,
            start=start.strftime("%d-%m-%Y"),
            end=end.strftime("%d-%m-%Y"),
        )
    ).json()

    return normalize(
        summary if isinstance(summary, dict) else {},
        announcements if isinstance(announcements, list) else [],
    )


# Stop a run after this many companies fail in a row; NSE is likely
# throttling or down, and retrying every company would take hours.
MAX_CONSECUTIVE_FAILURES = 5


def refresh_corporate_info(
    tickers: list[str],
    force: bool = False,
    limit: int | None = None,
    deadline: datetime | None = None,
) -> None:
    """
    Fetch corporate info for tickers not refreshed recently, stalest first.

    `limit` caps how many companies are fetched in one run and `deadline`
    (UTC) stops the run early, so a slow night can't hold up publishing.
    """
    provider = NSEFinancialResultsProvider()
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        securities = {
            security.ticker: security
            for security in session.exec(
                select(Security).where(
                    Security.ticker.in_(tickers),
                    Security.exchange == "NSE",
                )
            ).all()
        }

        fetched = {
            info.security_id: info.fetched_at.replace(tzinfo=timezone.utc)
            for info in session.exec(select(CorporateInfo)).all()
        }

    due = []

    for ticker in tickers:
        security = securities.get(ticker)

        if security is None:
            continue

        last = fetched.get(security.id)

        if force or last is None or now - last >= REFRESH_AFTER:
            due.append((last or datetime.min.replace(tzinfo=timezone.utc), ticker))

    # Never-fetched companies first, then the oldest.
    due.sort()
    queue = [ticker for _, ticker in due]

    if limit is not None:
        queue = queue[:limit]

    failures = 0

    for index, ticker in enumerate(queue, start=1):
        if deadline is not None and datetime.now(timezone.utc) >= deadline:
            print(f"Corporate refresh: time budget reached after {index - 1} companies.")
            break

        security = securities[ticker]

        try:
            data = load_corporate_info(provider, security)
        except Exception as exc:
            failures += 1
            print(f"[{index}/{len(queue)}] {ticker}: ERROR {exc}", flush=True)

            if failures >= MAX_CONSECUTIVE_FAILURES:
                print("Corporate refresh: too many failures in a row, stopping.")
                break

            continue

        failures = 0

        with Session(engine) as session:
            info = session.get(CorporateInfo, security.id) or CorporateInfo(
                security_id=security.id,
                fetched_at=now,
            )
            info.fetched_at = datetime.now(timezone.utc)
            info.data = data

            session.add(info)
            session.commit()

        print(
            f"[{index}/{len(queue)}] {ticker}: "
            f"{len(data['announcements'])} announcements, "
            f"{len(data['shareholding'])} shareholding periods",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="*", default=[])
    parser.add_argument("--top", type=int, default=0)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if fetched recently",
    )
    args = parser.parse_args()

    create_db_and_tables()

    tickers = [t.upper() for t in args.tickers]

    with Session(engine) as session:
        for ticker in top_tickers_by_traded_value(session, args.top):
            if ticker not in tickers:
                tickers.append(ticker)

    if not tickers:
        raise SystemExit("Pass --tickers and/or --top.")

    refresh_corporate_info(tickers, force=args.force)


if __name__ == "__main__":
    main()
