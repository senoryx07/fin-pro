import argparse
from datetime import date, timedelta

from sqlalchemy import func
from sqlmodel import Session, select

from backend.app.database.database import (
    create_db_and_tables,
    engine,
)
from backend.app.models.financials import FinancialResult
from backend.app.models.market_data import DailyPrice
from backend.app.models.security import Security
from backend.app.providers.nse_financial_data import (
    NSEFinancialResultsProvider,
)


DEFAULT_SINCE = date(2018, 4, 1)


def top_tickers_by_traded_value(
    session: Session,
    limit: int,
    lookback_days: int = 30,
) -> list[str]:
    latest = session.exec(
        select(func.max(DailyPrice.trade_date))
    ).one()

    if latest is None:
        return []

    rows = session.exec(
        select(
            Security.ticker,
            func.avg(DailyPrice.traded_value),
        )
        .join(Security, Security.id == DailyPrice.security_id)
        .where(
            DailyPrice.trade_date >= latest - timedelta(days=lookback_days),
            Security.ticker.is_not(None),
        )
        .group_by(Security.ticker)
        .order_by(func.avg(DailyPrice.traded_value).desc())
        .limit(limit)
    ).all()

    return [ticker for ticker, _ in rows]


def load_company_financials(
    provider: NSEFinancialResultsProvider,
    ticker: str,
    since: date = DEFAULT_SINCE,
) -> dict[str, int]:
    ticker = ticker.strip().upper()

    with Session(engine) as session:
        security = session.exec(
            select(Security).where(
                Security.ticker == ticker,
                Security.exchange == "NSE",
            )
        ).first()

        if security is None:
            raise ValueError(f"Unknown NSE ticker: {ticker}")

        existing = {
            (result.period_end, result.consolidated): result
            for result in session.exec(
                select(FinancialResult).where(
                    FinancialResult.security_id == security.id
                )
            ).all()
        }

        filings = provider.list_filings(ticker)

        inserted = 0
        updated = 0
        skipped = 0
        failed = 0
        seen: set[tuple[date, bool]] = set()

        # Filings are newest-first, so the first one seen for a period is
        # its latest revision.
        for filing in filings:
            key = (filing["period_end"], filing["consolidated"])

            if filing["period_end"] < since or key in seen:
                continue

            seen.add(key)

            current = existing.get(key)

            if (
                current is not None
                and current.source_url == filing["xbrl_url"]
            ):
                skipped += 1
                continue

            try:
                result = provider.get_result(filing)
            except Exception as exc:
                print(f"  {ticker} {filing['period_end']}: {exc}")
                failed += 1
                continue

            if current is None:
                current = FinancialResult(
                    security_id=security.id,
                    **result,
                )
                inserted += 1
            else:
                for field, value in result.items():
                    setattr(current, field, value)
                updated += 1

            session.add(current)

        session.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load quarterly results from NSE XBRL filings.",
    )

    parser.add_argument(
        "--tickers",
        nargs="*",
        default=[],
        help="NSE tickers to load",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Also load the N most-traded stocks",
    )

    parser.add_argument(
        "--since",
        type=date.fromisoformat,
        default=DEFAULT_SINCE,
        help="Earliest quarter end to load (YYYY-MM-DD)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    create_db_and_tables()

    tickers = [ticker.upper() for ticker in args.tickers]

    if args.top:
        with Session(engine) as session:
            for ticker in top_tickers_by_traded_value(session, args.top):
                if ticker not in tickers:
                    tickers.append(ticker)

    if not tickers:
        raise SystemExit("Pass --tickers and/or --top.")

    provider = NSEFinancialResultsProvider()

    for index, ticker in enumerate(tickers, start=1):
        try:
            summary = load_company_financials(
                provider=provider,
                ticker=ticker,
                since=args.since,
            )
            print(f"[{index}/{len(tickers)}] {ticker}: {summary}", flush=True)
        except Exception as exc:
            print(f"[{index}/{len(tickers)}] {ticker}: ERROR {exc}", flush=True)
