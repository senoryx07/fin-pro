from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from backend.app.models.market_data import (
    DailyPrice,
    IndicatorAvailability,
    MovingAverage,
    PriceAdjustment,
    PricePoint,
    PriceSeriesResponse,
    TechnicalSnapshot,
)
from backend.app.models.security import Security
from backend.app.technicals import indicators


RETURN_PERIODS = {
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "1Y": 252,
}

MOVING_AVERAGE_PERIODS = (20, 50, 200)


def find_nse_security(
    session: Session,
    ticker: str,
) -> Security | None:
    return session.exec(
        select(Security).where(
            Security.ticker == ticker.strip().upper(),
            Security.exchange == "NSE",
        )
    ).first()


# Smallest bonus (1:10) and largest reverse split worth adjusting for.
# Ratios in between are dividends or trading-series switches and are
# left alone.
MIN_ADJUSTMENT_RATIO = 1.09
MAX_REVERSE_RATIO = 0.5


@dataclass
class PriceBar:
    """A daily price, adjusted for splits and bonuses."""

    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float
    previous_close: float | None
    volume: int | None


# NSE caps daily moves at 20% for stocks with price bands, so an overnight
# gap larger than this is a split or bonus rather than a real move.
GAP_THRESHOLD = 1 / 0.75

# Common split and bonus ratios (5:1 split = 5, 1:1 bonus = 2, ...).
STANDARD_RATIOS = (1.25, 4 / 3, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 10.0, 20.0)

RATIO_TOLERANCE = 0.10


def _standard_ratio(gap: float) -> float | None:
    nearest = min(STANDARD_RATIOS, key=lambda r: abs(gap / r - 1))

    return nearest if abs(gap / nearest - 1) <= RATIO_TOLERANCE else None


def find_adjustments(
    prices: list[DailyPrice],
) -> list[PriceAdjustment]:
    """
    Split and bonus adjustments, from two signals:

    - NSE sometimes reports the previous close already adjusted on the
      ex-date, so prior close / that figure is the exact factor.
    - Otherwise the ex-date shows as an overnight gap down far beyond the
      daily price band, which is snapped to the nearest standard ratio.
    """
    adjustments = []

    for previous, current in zip(prices, prices[1:]):
        ratio = None

        if current.previous_close:
            reported = previous.close / current.previous_close

            if (
                reported >= MIN_ADJUSTMENT_RATIO
                or reported <= MAX_REVERSE_RATIO
            ):
                ratio = reported

        reference = current.open or current.close

        if ratio is None and reference:
            gap = previous.close / reference

            if gap >= GAP_THRESHOLD:
                ratio = _standard_ratio(gap)

        if ratio is not None:
            adjustments.append(
                PriceAdjustment(
                    trade_date=current.trade_date,
                    ratio=ratio,
                )
            )

    return adjustments


def adjust_prices(
    prices: list[DailyPrice],
) -> tuple[list[PriceBar], list[PriceAdjustment]]:
    adjustments = find_adjustments(prices)

    bars: list[PriceBar] = []
    factor = 1.0
    pending = sorted(adjustments, key=lambda a: a.trade_date)

    # Walk backwards so every bar before an ex-date is divided by the
    # product of all later adjustment ratios.
    for price in reversed(prices):
        bars.append(
            PriceBar(
                trade_date=price.trade_date,
                open=_scale(price.open, factor),
                high=_scale(price.high, factor),
                low=_scale(price.low, factor),
                close=price.close / factor,
                previous_close=_scale(
                    price.previous_close,
                    factor,
                ),
                volume=(
                    round(price.volume * factor)
                    if price.volume is not None
                    else None
                ),
            )
        )

        while pending and pending[-1].trade_date == price.trade_date:
            factor *= pending.pop().ratio

    bars.reverse()

    return bars, adjustments


def _scale(
    value: float | None,
    factor: float,
) -> float | None:
    return value / factor if value is not None else None


def get_daily_prices(
    session: Session,
    security: Security,
) -> list[PriceBar]:
    """Split/bonus-adjusted daily prices with a close, oldest first."""
    return get_adjusted_prices(session, security)[0]


def get_adjusted_prices(
    session: Session,
    security: Security,
) -> tuple[list[PriceBar], list[PriceAdjustment]]:
    prices = list(
        session.exec(
            select(DailyPrice)
            .where(
                DailyPrice.security_id == security.id,
                DailyPrice.close.is_not(None),
            )
            .order_by(DailyPrice.trade_date)
        ).all()
    )

    return adjust_prices(prices)


def build_price_series(
    session: Session,
    ticker: str,
    limit: int | None = None,
) -> PriceSeriesResponse | None:
    security = find_nse_security(session, ticker)

    if security is None or security.ticker is None:
        return None

    prices, adjustments = get_adjusted_prices(session, security)
    closes = [price.close for price in prices]

    sma_20 = indicators.sma(closes, 20)
    upper, _, lower = indicators.bollinger_bands(closes, 20)

    points = [
        PricePoint(
            trade_date=price.trade_date,
            open=price.open,
            high=price.high,
            low=price.low,
            close=price.close,
            volume=price.volume,
            sma_20=sma_20[index],
            bollinger_upper=upper[index],
            bollinger_lower=lower[index],
        )
        for index, price in enumerate(prices)
    ]

    if limit is not None:
        points = points[-limit:]

    return PriceSeriesResponse(
        ticker=security.ticker,
        exchange=security.exchange,
        points=points,
        adjustments=adjustments,
    )


def build_technical_snapshot(
    session: Session,
    ticker: str,
) -> TechnicalSnapshot | None:
    security = find_nse_security(session, ticker)

    if security is None or security.ticker is None:
        return None

    prices = get_daily_prices(session, security)

    if not prices:
        return TechnicalSnapshot(
            ticker=security.ticker,
            sessions=0,
        )

    closes = [price.close for price in prices]
    latest = prices[-1]

    previous_close = latest.previous_close

    if previous_close is None and len(closes) > 1:
        previous_close = closes[-2]

    change = None
    change_percent = None

    if previous_close:
        change = latest.close - previous_close
        change_percent = change / previous_close

    highs = [p.high for p in prices if p.high is not None]
    lows = [p.low for p in prices if p.low is not None]
    volumes = [p.volume for p in prices if p.volume is not None]
    recent_volumes = volumes[-20:]

    moving_averages = []

    for period in MOVING_AVERAGE_PERIODS:
        sma_value = indicators.sma(closes, period)[-1]
        ema_value = indicators.ema(closes, period)[-1]

        moving_averages.append(
            MovingAverage(
                period=period,
                sma=sma_value,
                ema=ema_value,
                price_above_sma=(
                    latest.close > sma_value
                    if sma_value is not None
                    else None
                ),
            )
        )

    macd_line, signal_line, histogram = indicators.macd(closes)
    upper, middle, lower = indicators.bollinger_bands(closes)

    return TechnicalSnapshot(
        ticker=security.ticker,
        sessions=len(prices),
        first_date=prices[0].trade_date,
        as_of=latest.trade_date,
        last_close=latest.close,
        previous_close=previous_close,
        change=change,
        change_percent=change_percent,
        day_high=latest.high,
        day_low=latest.low,
        volume=latest.volume,
        period_high=max(highs) if highs else None,
        period_low=min(lows) if lows else None,
        average_volume_20=(
            sum(recent_volumes) / len(recent_volumes)
            if recent_volumes
            else None
        ),
        returns={
            label: indicators.period_return(closes, periods)
            for label, periods in RETURN_PERIODS.items()
        },
        volatility=indicators.annualized_volatility(closes),
        rsi_14=indicators.rsi(closes, 14)[-1],
        macd=macd_line[-1],
        macd_signal=signal_line[-1],
        macd_histogram=histogram[-1],
        bollinger_upper=upper[-1],
        bollinger_middle=middle[-1],
        bollinger_lower=lower[-1],
        moving_averages=moving_averages,
        availability=[
            IndicatorAvailability(
                name=name,
                required_sessions=required,
                available=len(prices) >= required,
            )
            for name, required in (
                ("RSI 14", 15),
                ("SMA 20 / Bollinger", 20),
                ("MACD 12/26/9", 34),
                ("SMA 50", 50),
                ("SMA 200", 200),
            )
        ],
    )
