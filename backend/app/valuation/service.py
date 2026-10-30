import statistics
from datetime import date, timedelta

from sqlmodel import Session

from backend.app.financials.service import (
    choose_basis,
    load_results,
    ratio,
    shares_outstanding,
    sum_field,
    trailing_four,
)
from backend.app.models.financials import (
    FinancialResult,
    PEPoint,
    ValuationResponse,
)
from backend.app.models.security import Security
from backend.app.technicals.service import get_daily_prices


# Used when a filing has no broadcast date; SEBI allows 45 days for
# quarterly results.
FILING_LAG = timedelta(days=45)


def available_from(result: FinancialResult) -> date:
    if result.filing_date is not None:
        return result.filing_date.date()

    return result.period_end + FILING_LAG


def ttm_eps_timeline(
    results: list[FinancialResult],
    current_shares: float | None,
) -> list[tuple[date, float]]:
    """
    (date known, TTM EPS) pairs on today's share count, which matches
    prices adjusted for splits and bonuses.
    """
    timeline = []

    for index, result in enumerate(results):
        window = trailing_four(results, index)

        if window is None:
            continue

        profit = sum_field(window, "net_profit_owners")
        eps = ratio(profit, current_shares)

        if eps is not None:
            timeline.append((available_from(result), eps))

    timeline.sort()

    return timeline


def build_valuation(
    session: Session,
    security: Security,
    basis: str | None = None,
) -> ValuationResponse:
    grouped = load_results(session, security)
    chosen = choose_basis(grouped, basis)
    results = grouped.get(chosen, []) if chosen else []

    prices = get_daily_prices(session, security)
    latest_price = prices[-1] if prices else None

    latest = results[-1] if results else None
    shares = shares_outstanding(latest) if latest else None
    ttm = trailing_four(results, len(results) - 1)

    ttm_profit = sum_field(ttm, "net_profit_owners") if ttm else None
    ttm_revenue = sum_field(ttm, "revenue") if ttm else None
    ttm_eps = ratio(ttm_profit, shares)

    price = latest_price.close if latest_price else None
    market_cap = price * shares if price is not None and shares else None

    pe_ratio = (
        ratio(price, ttm_eps)
        if ttm_eps is not None and ttm_eps > 0
        else None
    )

    timeline = ttm_eps_timeline(results, shares)
    pe_history: list[PEPoint] = []
    cursor = 0
    current_eps: float | None = None

    for point in prices:
        while (
            cursor < len(timeline)
            and timeline[cursor][0] <= point.trade_date
        ):
            current_eps = timeline[cursor][1]
            cursor += 1

        if current_eps is not None and current_eps > 0:
            pe_history.append(
                PEPoint(
                    trade_date=point.trade_date,
                    pe_ratio=point.close / current_eps,
                )
            )

    pe_values = [p.pe_ratio for p in pe_history]

    return ValuationResponse(
        ticker=security.ticker or "",
        basis=chosen,
        price=price,
        price_date=latest_price.trade_date if latest_price else None,
        shares_outstanding=shares,
        market_cap=market_cap,
        ttm_eps=ttm_eps,
        pe_ratio=pe_ratio,
        earnings_yield=ratio(ttm_eps, price),
        price_to_sales=ratio(market_cap, ttm_revenue),
        pe_history=pe_history,
        pe_median=statistics.median(pe_values) if pe_values else None,
        pe_low=min(pe_values) if pe_values else None,
        pe_high=max(pe_values) if pe_values else None,
    )
