from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from backend.app.models.financials import (
    AnnualResult,
    FinancialResult,
    FundamentalsResponse,
    QuarterlyResult,
)
from backend.app.models.security import Security


CONSOLIDATED = "consolidated"
STANDALONE = "standalone"


def ratio(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    if numerator is None or not denominator:
        return None

    return numerator / denominator


def growth(
    current: float | None,
    previous: float | None,
) -> float | None:
    # Growth off a negative or zero base is not meaningful.
    if current is None or previous is None or previous <= 0:
        return None

    return current / previous - 1


STANDARD_FACE_VALUES = (1.0, 2.0, 5.0, 10.0, 100.0)

SHARE_COUNT_TOLERANCE = 0.25


def shares_outstanding(result: FinancialResult) -> float | None:
    """
    Paid-up capital / face value, sanity-checked against the share count
    implied by profit / EPS, since filings occasionally misreport the
    face value.
    """
    reported = None

    if result.face_value and 0 < result.face_value <= 1000:
        reported = ratio(result.paid_up_capital, result.face_value)

    implied = None

    if (
        result.eps_basic is not None
        and abs(result.eps_basic) >= 0.05
        and result.net_profit_owners
    ):
        implied = abs(result.net_profit_owners / result.eps_basic)

    if implied is None:
        return reported

    def close_to_implied(shares: float | None) -> bool:
        return (
            shares is not None
            and abs(shares / implied - 1) <= SHARE_COUNT_TOLERANCE
        )

    if close_to_implied(reported):
        return reported

    if result.paid_up_capital:
        for face_value in STANDARD_FACE_VALUES:
            shares = result.paid_up_capital / face_value

            if close_to_implied(shares):
                return shares

    return implied


def fiscal_year_label(period_end: date) -> str:
    """Indian fiscal year label: Apr-2025..Mar-2026 is FY26."""
    year = period_end.year + (1 if period_end.month > 3 else 0)

    return f"FY{year % 100:02d}"


def load_results(
    session: Session,
    security: Security,
) -> dict[str, list[FinancialResult]]:
    """Results grouped by basis, oldest first."""
    results = session.exec(
        select(FinancialResult)
        .where(FinancialResult.security_id == security.id)
        .order_by(FinancialResult.period_end)
    ).all()

    grouped: dict[str, list[FinancialResult]] = {
        CONSOLIDATED: [],
        STANDALONE: [],
    }

    for result in results:
        basis = CONSOLIDATED if result.consolidated else STANDALONE
        grouped[basis].append(result)

    return {basis: rows for basis, rows in grouped.items() if rows}


def choose_basis(
    grouped: dict[str, list[FinancialResult]],
    requested: str | None = None,
) -> str | None:
    if requested in grouped:
        return requested

    if not grouped:
        return None

    if CONSOLIDATED not in grouped:
        return STANDALONE

    if STANDALONE not in grouped:
        return CONSOLIDATED

    # Prefer consolidated unless it is stale relative to standalone.
    latest_consolidated = grouped[CONSOLIDATED][-1].period_end
    latest_standalone = grouped[STANDALONE][-1].period_end

    if latest_consolidated >= latest_standalone:
        return CONSOLIDATED

    return STANDALONE


def trailing_four(
    results: list[FinancialResult],
    end_index: int,
) -> list[FinancialResult] | None:
    """The four consecutive quarters ending at `end_index`, if available."""
    if end_index < 3:
        return None

    window = results[end_index - 3:end_index + 1]

    span = window[-1].period_end - window[0].period_start

    # Four contiguous quarters span just under a year.
    if span > timedelta(days=370):
        return None

    return window


def sum_field(
    rows: list[FinancialResult],
    field: str,
) -> float | None:
    values = [getattr(row, field) for row in rows]

    if any(value is None for value in values):
        return None

    return sum(values)


def build_quarterly(
    results: list[FinancialResult],
    current_shares: float | None,
) -> list[QuarterlyResult]:
    by_end = {result.period_end: result for result in results}
    quarters = []

    for result in results:
        year_ago = by_end.get(
            date(
                result.period_end.year - 1,
                result.period_end.month,
                result.period_end.day,
            )
        )

        operating_profit = None

        if (
            not result.is_bank
            and result.revenue is not None
            and result.expenses is not None
        ):
            # EBITDA, excluding other income.
            operating_profit = (
                result.revenue
                - result.expenses
                + (result.finance_costs or 0)
                + (result.depreciation or 0)
            )

        quarters.append(
            QuarterlyResult(
                period_end=result.period_end,
                revenue=result.revenue,
                other_income=result.other_income,
                expenses=result.expenses,
                operating_profit=operating_profit,
                operating_margin=ratio(operating_profit, result.revenue),
                finance_costs=result.finance_costs,
                depreciation=result.depreciation,
                profit_before_tax=result.profit_before_tax,
                tax=result.tax,
                net_profit_owners=result.net_profit_owners,
                net_margin=ratio(result.net_profit_owners, result.revenue),
                eps_basic=result.eps_basic,
                adjusted_eps=ratio(result.net_profit_owners, current_shares),
                revenue_growth_yoy=growth(
                    result.revenue,
                    year_ago.revenue if year_ago else None,
                ),
                profit_growth_yoy=growth(
                    result.net_profit_owners,
                    year_ago.net_profit_owners if year_ago else None,
                ),
            )
        )

    return quarters


def build_annual(
    results: list[FinancialResult],
    current_shares: float | None,
) -> list[AnnualResult]:
    """Fiscal years (Apr-Mar) with all four quarters reported."""
    years: dict[str, list[FinancialResult]] = {}

    for result in results:
        years.setdefault(
            fiscal_year_label(result.period_end), []
        ).append(result)

    annual: list[AnnualResult] = []

    for label, rows in years.items():
        if len(rows) != 4:
            continue

        revenue = sum_field(rows, "revenue")
        profit = sum_field(rows, "net_profit_owners")
        previous = annual[-1] if annual else None

        if previous and previous.period_end.year != rows[-1].period_end.year - 1:
            previous = None

        annual.append(
            AnnualResult(
                fiscal_year=label,
                period_end=rows[-1].period_end,
                revenue=revenue,
                net_profit_owners=profit,
                net_margin=ratio(profit, revenue),
                adjusted_eps=ratio(profit, current_shares),
                revenue_growth=growth(
                    revenue, previous.revenue if previous else None
                ),
                profit_growth=growth(
                    profit, previous.net_profit_owners if previous else None
                ),
            )
        )

    return annual


def build_fundamentals(
    session: Session,
    security: Security,
    basis: str | None = None,
) -> FundamentalsResponse:
    grouped = load_results(session, security)
    chosen = choose_basis(grouped, basis)
    results = grouped.get(chosen, []) if chosen else []

    latest = results[-1] if results else None
    current_shares = shares_outstanding(latest) if latest else None
    ttm = trailing_four(results, len(results) - 1)

    ttm_revenue = sum_field(ttm, "revenue") if ttm else None
    ttm_profit = sum_field(ttm, "net_profit_owners") if ttm else None

    last_filed: datetime | None = max(
        (r.filing_date for r in results if r.filing_date),
        default=None,
    )

    return FundamentalsResponse(
        ticker=security.ticker or "",
        basis=chosen,
        available_bases=list(grouped),
        is_bank=bool(latest and latest.is_bank),
        shares_outstanding=current_shares,
        latest_period=latest.period_end if latest else None,
        last_filed=last_filed,
        ttm_revenue=ttm_revenue,
        ttm_net_profit=ttm_profit,
        ttm_eps=ratio(ttm_profit, current_shares),
        ttm_net_margin=ratio(ttm_profit, ttm_revenue),
        quarters=build_quarterly(results, current_shares),
        annual=build_annual(results, current_shares),
    )
