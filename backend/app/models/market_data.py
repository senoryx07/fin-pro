from datetime import date

from sqlmodel import Field, SQLModel
from sqlalchemy import Index, UniqueConstraint


class DailyPrice(SQLModel, table=True):
    __tablename__ = "daily_prices"

    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "trade_date",
            name="uq_daily_price_security_date",
        ),
        Index(
            "ix_daily_prices_security_date",
            "security_id",
            "trade_date",
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

    trade_date: date = Field(
        index=True,
    )

    open: float | None = None

    high: float | None = None

    low: float | None = None

    close: float | None = None

    previous_close: float | None = None

    last_price: float | None = None

    volume: int | None = None

    traded_value: float | None = None

    source: str = Field(
        default="NSE",
        index=True,
    )

class PricePoint(SQLModel):
    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None
    sma_20: float | None
    bollinger_upper: float | None
    bollinger_lower: float | None


class PriceSeriesResponse(SQLModel):
    ticker: str
    exchange: str
    points: list[PricePoint]


class MovingAverage(SQLModel):
    period: int
    sma: float | None
    ema: float | None
    price_above_sma: bool | None


class IndicatorAvailability(SQLModel):
    name: str
    required_sessions: int
    available: bool


class TechnicalSnapshot(SQLModel):
    ticker: str
    sessions: int
    first_date: date | None = None
    as_of: date | None = None

    last_close: float | None = None
    previous_close: float | None = None
    change: float | None = None
    change_percent: float | None = None

    day_high: float | None = None
    day_low: float | None = None
    volume: int | None = None

    period_high: float | None = None
    period_low: float | None = None
    average_volume_20: float | None = None

    returns: dict[str, float | None] = {}
    volatility: float | None = None

    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None

    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None

    moving_averages: list[MovingAverage] = []
    availability: list[IndicatorAvailability] = []
