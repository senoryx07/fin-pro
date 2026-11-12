"""
Daily refresh: new NSE prices, new quarterly results, static export.

    python -m backend.app.update
    python -m backend.app.update --top 200     # also add more companies
"""

import argparse
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from backend.app.database.database import create_db_and_tables, engine
from backend.app.export.static_site import DEFAULT_OUTPUT, export_site
from backend.app.ingestion.classification_loader import (
    load_classification,
)
from backend.app.ingestion.corporate_loader import refresh_corporate_info
from backend.app.ingestion.financial_loader import (
    load_company_financials,
    top_tickers_by_traded_value,
)
from backend.app.ingestion.market_loader import backfill_nse_history
from backend.app.models.financials import FinancialResult
from backend.app.models.market_data import DailyPrice
from backend.app.models.security import Security
from backend.app.providers.nse_financial_data import (
    NSEFinancialResultsProvider,
)


def tickers_with_financials(session: Session) -> list[str]:
    return list(
        session.exec(
            select(Security.ticker)
            .join(
                FinancialResult,
                FinancialResult.security_id == Security.id,
            )
            .distinct()
        ).all()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Also load results for the N most-traded stocks",
    )
    parser.add_argument("--skip-prices", action="store_true")
    parser.add_argument("--skip-financials", action="store_true")
    parser.add_argument("--skip-corporate", action="store_true")
    parser.add_argument(
        "--corporate-top",
        type=int,
        default=800,
        help="Refresh announcements/shareholding for the N most-traded",
    )
    parser.add_argument(
        "--corporate-limit",
        type=int,
        default=250,
        help="At most this many announcement refreshes per run (stalest first)",
    )
    parser.add_argument(
        "--budget-minutes",
        type=int,
        default=75,
        help="Time allowed for results + announcements before exporting",
    )
    args = parser.parse_args()

    create_db_and_tables()

    if not args.skip_prices:
        with Session(engine) as session:
            latest = session.exec(
                select(func.max(DailyPrice.trade_date))
            ).one()

        start = latest + timedelta(days=1) if latest else date.today()

        if start <= date.today():
            backfill_nse_history(start_date=start, end_date=date.today())

    # Prices are essential; results and announcements get a fixed time
    # budget so a slow night still ends with a published site.
    deadline = datetime.now(timezone.utc) + timedelta(minutes=args.budget_minutes)

    if not args.skip_financials:
        with Session(engine) as session:
            tickers = tickers_with_financials(session)

            for ticker in top_tickers_by_traded_value(session, args.top):
                if ticker not in tickers:
                    tickers.append(ticker)

        provider = NSEFinancialResultsProvider()
        failures = 0

        for index, ticker in enumerate(tickers, start=1):
            if datetime.now(timezone.utc) >= deadline:
                print(f"Results: time budget reached after {index - 1} companies.")
                break

            try:
                summary = load_company_financials(provider, ticker)
                failures = 0
            except Exception as exc:
                summary = f"ERROR {exc}"
                failures += 1

            print(f"[{index}/{len(tickers)}] {ticker}: {summary}", flush=True)

            if failures >= 5:
                print("Results: too many failures in a row, stopping.")
                break

    if not args.skip_corporate:
        with Session(engine) as session:
            corporate_tickers = top_tickers_by_traded_value(
                session, args.corporate_top
            )

        refresh_corporate_info(
            corporate_tickers,
            limit=args.corporate_limit,
            deadline=deadline,
        )

    try:
        load_classification()
    except Exception as exc:
        print(f"Classification skipped: {exc}")

    export_site(DEFAULT_OUTPUT)


if __name__ == "__main__":
    main()
