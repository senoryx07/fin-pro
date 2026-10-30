from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class FinancialResult(SQLModel, table=True):
    """
    One quarterly results filing. All amounts are in rupees.
    """

    __tablename__ = "financial_results"

    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "period_end",
            "consolidated",
            name="uq_financial_result_period",
        ),
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    security_id: int = Field(
        foreign_key="securities.id",
        index=True,
    )

    period_start: date

    period_end: date = Field(
        index=True,
    )

    consolidated: bool = Field(
        index=True,
    )

    audited: bool | None = None

    is_bank: bool = False

    filing_date: datetime | None = None

    revenue: float | None = None

    other_income: float | None = None

    total_income: float | None = None

    expenses: float | None = None

    finance_costs: float | None = None

    depreciation: float | None = None

    profit_before_tax: float | None = None

    tax: float | None = None

    net_profit: float | None = None

    net_profit_owners: float | None = None

    eps_basic: float | None = None

    eps_diluted: float | None = None

    paid_up_capital: float | None = None

    face_value: float | None = None

    source: str = Field(
        default="NSE",
    )

    source_url: str | None = None


class QuarterlyResult(SQLModel):
    period_end: date
    revenue: float | None
    other_income: float | None
    expenses: float | None
    operating_profit: float | None
    operating_margin: float | None
    finance_costs: float | None
    depreciation: float | None
    profit_before_tax: float | None
    tax: float | None
    net_profit_owners: float | None
    net_margin: float | None
    eps_basic: float | None
    adjusted_eps: float | None
    revenue_growth_yoy: float | None
    profit_growth_yoy: float | None


class AnnualResult(SQLModel):
    fiscal_year: str
    period_end: date
    revenue: float | None
    net_profit_owners: float | None
    net_margin: float | None
    adjusted_eps: float | None
    revenue_growth: float | None
    profit_growth: float | None


class FundamentalsResponse(SQLModel):
    ticker: str
    basis: str | None
    available_bases: list[str]
    is_bank: bool
    shares_outstanding: float | None
    latest_period: date | None
    last_filed: datetime | None

    ttm_revenue: float | None
    ttm_net_profit: float | None
    ttm_eps: float | None
    ttm_net_margin: float | None

    quarters: list[QuarterlyResult]
    annual: list[AnnualResult]


class PEPoint(SQLModel):
    trade_date: date
    pe_ratio: float


class ValuationResponse(SQLModel):
    ticker: str
    basis: str | None
    price: float | None
    price_date: date | None
    shares_outstanding: float | None
    market_cap: float | None
    ttm_eps: float | None
    pe_ratio: float | None
    earnings_yield: float | None
    price_to_sales: float | None
    pe_history: list[PEPoint]
    pe_median: float | None
    pe_low: float | None
    pe_high: float | None
