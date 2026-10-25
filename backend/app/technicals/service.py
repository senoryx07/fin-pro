from sqlmodel import Session, select

from backend.app.models.market_data import (
    DailyPrice,
    IndicatorAvailability,
    MovingAverage,
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


def get_daily_prices(
    session: Session,
    security: Security,
    limit: int | None = None,
) -> list[DailyPrice]:
    """Daily prices with a close, oldest first, optionally the latest `limit`."""
    statement = (
        select(DailyPrice)
        .where(
            DailyPrice.security_id == security.id,
            DailyPrice.close.is_not(None),
        )
        .order_by(DailyPrice.trade_date.desc())
    )

    if limit is not None:
        statement = statement.limit(limit)

    prices = list(session.exec(statement).all())
    prices.reverse()

    return prices


def build_price_series(
    session: Session,
    ticker: str,
    limit: int | None = None,
) -> PriceSeriesResponse | None:
    security = find_nse_security(session, ticker)

    if security is None or security.ticker is None:
        return None

    prices = get_daily_prices(session, security)
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
