"""
Export the database as static JSON for the GitHub Pages site.

    python -m backend.app.export.static_site

Writes frontend/public/data/index.json (search index) and one
frontend/public/data/companies/{TICKER}.json per company with prices.
"""

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, select

from backend.app.database.database import engine
from backend.app.financials.service import build_fundamentals
from backend.app.models.company import Company
from backend.app.models.corporate import CorporateInfo
from backend.app.models.financials import FinancialResult
from backend.app.models.market_data import DailyPrice
from backend.app.models.security import Security
from backend.app.research.company_service import build_company_response
from backend.app.technicals.service import (
    build_price_series,
    build_technical_snapshot,
)
from backend.app.valuation.service import build_valuation


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[3] / "frontend" / "public" / "data"
)


def _round(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def columnar_prices(series) -> dict[str, list[Any]]:
    """Price points as parallel arrays, which is far smaller than objects."""
    points = series.points

    return {
        "date": [p.trade_date.isoformat() for p in points],
        "open": [_round(p.open) for p in points],
        "high": [_round(p.high) for p in points],
        "low": [_round(p.low) for p in points],
        "close": [_round(p.close) for p in points],
        "volume": [p.volume for p in points],
        "sma_20": [_round(p.sma_20) for p in points],
        "bollinger_upper": [_round(p.bollinger_upper) for p in points],
        "bollinger_lower": [_round(p.bollinger_lower) for p in points],
    }


def average_traded_value(
    session: Session,
    latest_trade_date,
    lookback_days: int = 30,
) -> dict[int, float]:
    if latest_trade_date is None:
        return {}

    rows = session.exec(
        select(
            DailyPrice.security_id,
            func.avg(DailyPrice.traded_value),
        )
        .where(
            DailyPrice.trade_date
            >= latest_trade_date - timedelta(days=lookback_days)
        )
        .group_by(DailyPrice.security_id)
    ).all()

    return {security_id: value for security_id, value in rows if value}


def export_company(
    session: Session,
    company: Company,
    security: Security,
) -> dict[str, Any] | None:
    series = build_price_series(session, security.ticker)

    if series is None or not series.points:
        return None

    technicals = build_technical_snapshot(session, security.ticker)
    fundamentals = build_fundamentals(session, security)
    valuation = build_valuation(session, security)
    corporate = session.get(CorporateInfo, security.id)

    valuation_data = valuation.model_dump(mode="json", exclude={"pe_history"})
    valuation_data["pe_history"] = {
        "date": [p.trade_date.isoformat() for p in valuation.pe_history],
        "pe": [_round(p.pe_ratio) for p in valuation.pe_history],
    }

    profile = build_company_response(company, security).model_dump(
        mode="json"
    )

    # The seed data uses a placeholder until a real profile exists; the
    # site writes its own summary instead.
    if profile["description"].startswith("Company profile pending"):
        profile["description"] = None

    return {
        "company": profile,
        "prices": columnar_prices(series),
        "adjustments": [
            a.model_dump(mode="json") for a in series.adjustments
        ],
        "technicals": technicals.model_dump(mode="json"),
        "fundamentals": (
            fundamentals.model_dump(mode="json")
            if fundamentals.basis
            else None
        ),
        "valuation": valuation_data if fundamentals.basis else None,
        "corporate": corporate.data if corporate else None,
    }


def summarize(
    company: Company,
    security: Security,
    data: dict[str, Any],
    traded_value: float | None,
    has_financials: bool,
) -> dict[str, Any]:
    """One row of the search index, also used for peer comparison."""
    technicals = data["technicals"]
    valuation = data["valuation"] or {}
    fundamentals = data["fundamentals"] or {}
    quarters = fundamentals.get("quarters") or [{}]

    return {
        "ticker": security.ticker,
        "name": company.name,
        "sector": company.sector,
        "industry": company.industry,
        "last_close": technicals["last_close"],
        "change_percent": technicals["change_percent"],
        "return_1y": technicals["returns"].get("1Y"),
        "market_cap": valuation.get("market_cap"),
        "pe_ratio": valuation.get("pe_ratio"),
        "ttm_revenue": fundamentals.get("ttm_revenue"),
        "ttm_net_margin": fundamentals.get("ttm_net_margin"),
        "revenue_growth": quarters[-1].get("revenue_growth_yoy"),
        "profit_growth": quarters[-1].get("profit_growth_yoy"),
        "avg_traded_value": _round(traded_value, 0),
        "has_financials": has_financials,
    }


def build_peer_groups(
    index: list[dict[str, Any]],
    size: int = 10,
    min_group: int = 4,
) -> dict[str, dict[str, Any]]:
    """
    Peers from the same industry (or sector when the industry is too
    small). `index` must already be sorted largest first.
    """
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for entry in index:
        for field in ("industry", "sector"):
            value = entry[field]

            if value and value != "Unclassified":
                by_key.setdefault((field, value), []).append(entry)

    groups = {}

    for entry in index:
        for field in ("industry", "sector"):
            members = by_key.get((field, entry[field]), [])

            if len(members) >= min_group:
                break
        else:
            continue

        top = members[:size]

        # Always include the company itself.
        if entry not in top:
            top = top[: size - 1] + [entry]

        groups[entry["ticker"]] = {
            "group": entry[field],
            "group_size": len(members),
            "companies": top,
        }

    return groups


def export_site(output: Path) -> None:
    companies_dir = output / "companies"

    if companies_dir.exists():
        shutil.rmtree(companies_dir)

    companies_dir.mkdir(parents=True)

    index: list[dict[str, Any]] = []

    with Session(engine) as session:
        latest_trade_date = session.exec(
            select(func.max(DailyPrice.trade_date))
        ).one()

        traded_value = average_traded_value(session, latest_trade_date)

        with_financials = set(
            session.exec(
                select(FinancialResult.security_id).distinct()
            ).all()
        )

        rows = session.exec(
            select(Company, Security)
            .join(Security, Security.company_id == Company.id)
            .where(
                Security.exchange == "NSE",
                Security.ticker.is_not(None),
            )
        ).all()

        exported: list[tuple[str, dict[str, Any]]] = []

        for count, (company, security) in enumerate(rows, start=1):
            data = export_company(session, company, security)

            if data is None:
                continue

            exported.append((security.ticker, data))
            index.append(
                summarize(
                    company,
                    security,
                    data,
                    traded_value.get(security.id),
                    security.id in with_financials,
                )
            )

            if count % 250 == 0:
                print(f"  {count}/{len(rows)} companies", flush=True)

    # Largest first; companies without a market cap by liquidity.
    index.sort(
        key=lambda c: (
            -(c["market_cap"] or 0),
            -(c["avg_traded_value"] or 0),
        )
    )

    peers = build_peer_groups(index)

    for ticker, data in exported:
        data["peers"] = peers.get(ticker)

        (companies_dir / f"{ticker}.json").write_text(
            json.dumps(data, separators=(",", ":")),
            encoding="utf-8",
        )

    (output / "index.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "latest_trade_date": (
                    latest_trade_date.isoformat()
                    if latest_trade_date
                    else None
                ),
                "companies": index,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    size = sum(p.stat().st_size for p in output.rglob("*.json"))

    print(
        f"Exported {len(index)} companies "
        f"({sum(c['has_financials'] for c in index)} with financials), "
        f"{size / 1e6:.1f} MB to {output}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    export_site(args.output)
