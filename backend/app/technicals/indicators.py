"""Pure-Python technical indicators.

Every series function returns a list aligned with its input, using
None wherever there is not yet enough history to compute a value.
"""

import math
from collections.abc import Sequence


TRADING_DAYS_PER_YEAR = 252


def sma(
    values: Sequence[float],
    period: int,
) -> list[float | None]:
    if period <= 0:
        raise ValueError("Period must be positive.")

    result: list[float | None] = []
    window_sum = 0.0

    for index, value in enumerate(values):
        window_sum += value

        if index >= period:
            window_sum -= values[index - period]

        if index >= period - 1:
            result.append(window_sum / period)
        else:
            result.append(None)

    return result


def ema(
    values: Sequence[float],
    period: int,
) -> list[float | None]:
    """Exponential moving average, seeded with the SMA of the first window."""
    if period <= 0:
        raise ValueError("Period must be positive.")

    result: list[float | None] = [None] * len(values)

    if len(values) < period:
        return result

    multiplier = 2 / (period + 1)
    previous = sum(values[:period]) / period
    result[period - 1] = previous

    for index in range(period, len(values)):
        previous = (
            (values[index] - previous) * multiplier
            + previous
        )
        result[index] = previous

    return result


def rsi(
    values: Sequence[float],
    period: int = 14,
) -> list[float | None]:
    """Relative Strength Index using Wilder's smoothing."""
    if period <= 0:
        raise ValueError("Period must be positive.")

    result: list[float | None] = [None] * len(values)

    if len(values) <= period:
        return result

    gains = 0.0
    losses = 0.0

    for index in range(1, period + 1):
        change = values[index] - values[index - 1]
        gains += max(change, 0.0)
        losses += max(-change, 0.0)

    average_gain = gains / period
    average_loss = losses / period
    result[period] = _rsi_value(average_gain, average_loss)

    for index in range(period + 1, len(values)):
        change = values[index] - values[index - 1]

        average_gain = (
            average_gain * (period - 1)
            + max(change, 0.0)
        ) / period

        average_loss = (
            average_loss * (period - 1)
            + max(-change, 0.0)
        ) / period

        result[index] = _rsi_value(average_gain, average_loss)

    return result


def _rsi_value(
    average_gain: float,
    average_loss: float,
) -> float:
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0

    relative_strength = average_gain / average_loss

    return 100 - 100 / (1 + relative_strength)


def macd(
    values: Sequence[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[
    list[float | None],
    list[float | None],
    list[float | None],
]:
    """Returns (macd line, signal line, histogram)."""
    fast = ema(values, fast_period)
    slow = ema(values, slow_period)

    macd_line: list[float | None] = [
        f - s if f is not None and s is not None else None
        for f, s in zip(fast, slow)
    ]

    signal_line: list[float | None] = [None] * len(values)
    defined = [
        (index, value)
        for index, value in enumerate(macd_line)
        if value is not None
    ]

    signal_values = ema(
        [value for _, value in defined],
        signal_period,
    )

    for (index, _), signal in zip(defined, signal_values):
        signal_line[index] = signal

    histogram: list[float | None] = [
        m - s if m is not None and s is not None else None
        for m, s in zip(macd_line, signal_line)
    ]

    return macd_line, signal_line, histogram


def bollinger_bands(
    values: Sequence[float],
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[
    list[float | None],
    list[float | None],
    list[float | None],
]:
    """Returns (upper band, middle band, lower band)."""
    middle = sma(values, period)
    upper: list[float | None] = [None] * len(values)
    lower: list[float | None] = [None] * len(values)

    for index, mean in enumerate(middle):
        if mean is None:
            continue

        window = values[index - period + 1:index + 1]
        variance = sum((v - mean) ** 2 for v in window) / period
        deviation = math.sqrt(variance)

        upper[index] = mean + num_std * deviation
        lower[index] = mean - num_std * deviation

    return upper, middle, lower


def daily_returns(
    values: Sequence[float],
) -> list[float]:
    return [
        values[index] / values[index - 1] - 1
        for index in range(1, len(values))
        if values[index - 1]
    ]


def annualized_volatility(
    values: Sequence[float],
) -> float | None:
    """Annualised standard deviation of daily returns (sample stdev)."""
    returns = daily_returns(values)

    if len(returns) < 2:
        return None

    mean = sum(returns) / len(returns)
    variance = sum(
        (r - mean) ** 2 for r in returns
    ) / (len(returns) - 1)

    return math.sqrt(variance) * math.sqrt(TRADING_DAYS_PER_YEAR)


def period_return(
    values: Sequence[float],
    periods: int,
) -> float | None:
    """Return over the last `periods` trading sessions."""
    if periods <= 0 or len(values) <= periods:
        return None

    start = values[-periods - 1]

    if not start:
        return None

    return values[-1] / start - 1
