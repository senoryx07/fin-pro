import argparse
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session, select

from backend.app.database.database import engine
from backend.app.models.market_data import DailyPrice
from backend.app.models.security import Security
from backend.app.providers.nse_market_data import (
    NSEMarketDataProvider,
)


SUPPORTED_SERIES = {
    "EQ",
    "BE",
    "BZ",
}


def find_security(
    session: Session,
    ticker: str,
    series: str | None,
) -> Security | None:
    ticker = ticker.strip().upper()

    securities = session.exec(
        select(Security).where(
            Security.ticker == ticker,
            Security.exchange == "NSE",
        )
    ).all()

    if not securities:
        return None

    if series:
        series = series.strip().upper()

        for security in securities:
            if (
                security.series
                and security.series.upper()
                == series
            ):
                return security

    return securities[0]


def upsert_daily_price(
    session: Session,
    security: Security,
    record: dict[str, Any],
) -> bool:
    trade_date = record["trade_date"]

    existing = session.exec(
        select(DailyPrice).where(
            DailyPrice.security_id == security.id,
            DailyPrice.trade_date == trade_date,
        )
    ).first()

    if existing is not None:
        existing.open = record["open"]
        existing.high = record["high"]
        existing.low = record["low"]
        existing.close = record["close"]
        existing.previous_close = record[
            "previous_close"
        ]
        existing.last_price = record[
            "last_price"
        ]
        existing.volume = record["volume"]
        existing.traded_value = record[
            "traded_value"
        ]
        existing.source = "NSE"

        session.add(existing)

        return False

    daily_price = DailyPrice(
        security_id=security.id,
        trade_date=trade_date,
        open=record["open"],
        high=record["high"],
        low=record["low"],
        close=record["close"],
        previous_close=record[
            "previous_close"
        ],
        last_price=record[
            "last_price"
        ],
        volume=record["volume"],
        traded_value=record[
            "traded_value"
        ],
        source="NSE",
    )

    session.add(daily_price)

    return True


def load_nse_daily_prices(
    trade_date: date,
    provider: NSEMarketDataProvider,
) -> dict[str, int]:
    print(
        f"Processing {trade_date.isoformat()}..."
    )

    records = provider.get_daily_prices(
        trade_date=trade_date
    )

    inserted = 0
    updated = 0
    skipped = 0

    with Session(engine) as session:

        for record in records:

            ticker = record.get("ticker")

            if not ticker:
                skipped += 1
                continue

            series = record.get("series")

            if series:
                series = series.strip().upper()

            if (
                series
                and series not in SUPPORTED_SERIES
            ):
                skipped += 1
                continue

            security = find_security(
                session=session,
                ticker=ticker,
                series=series,
            )

            if security is None:
                skipped += 1
                continue

            was_inserted = upsert_daily_price(
                session=session,
                security=security,
                record=record,
            )

            if was_inserted:
                inserted += 1
            else:
                updated += 1

        session.commit()

    return {
        "received": len(records),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }


def is_weekday(
    current_date: date,
) -> bool:
    return current_date.weekday() < 5


def backfill_nse_history(
    start_date: date,
    end_date: date,
) -> None:
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
        )

    print()
    print("========================================")
    print("FIN PRO - NSE HISTORICAL BACKFILL")
    print("========================================")
    print()
    print(
        f"Start date: {start_date.isoformat()}"
    )
    print(
        f"End date:   {end_date.isoformat()}"
    )
    print()

    provider = NSEMarketDataProvider()

    current_date = start_date

    trading_days = 0
    files_processed = 0

    total_received = 0
    total_inserted = 0
    total_updated = 0
    total_skipped = 0

    while current_date <= end_date:

        if not is_weekday(current_date):
            current_date += timedelta(days=1)
            continue

        try:
            result = load_nse_daily_prices(
                trade_date=current_date,
                provider=provider,
            )

            trading_days += 1
            files_processed += 1

            total_received += result[
                "received"
            ]

            total_inserted += result[
                "inserted"
            ]

            total_updated += result[
                "updated"
            ]

            total_skipped += result[
                "skipped"
            ]

        except FileNotFoundError:
            print(
                f"  No NSE file available for "
                f"{current_date.isoformat()}. "
                f"Skipping."
            )

        except Exception as exc:
            print(
                f"  ERROR for "
                f"{current_date.isoformat()}: "
                f"{exc}"
            )

        current_date += timedelta(days=1)

    print()
    print("========================================")
    print("HISTORICAL BACKFILL COMPLETE")
    print("========================================")
    print(
        f"Trading days processed: {trading_days}"
    )
    print(
        f"Files processed:        {files_processed}"
    )
    print(
        f"Rows received:          {total_received}"
    )
    print(
        f"Rows inserted:          {total_inserted}"
    )
    print(
        f"Rows updated:           {total_updated}"
    )
    print(
        f"Rows skipped:           {total_skipped}"
    )
    print("========================================")
    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill NSE daily prices.",
    )

    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        required=True,
        help="First trade date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=date.today(),
        help="Last trade date (YYYY-MM-DD), default today",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    backfill_nse_history(
        start_date=args.start,
        end_date=args.end,
    )
