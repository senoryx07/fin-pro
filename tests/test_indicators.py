import math

import pandas as pd
import pytest

from backend.app.technicals import indicators


CLOSES = [
    100.0, 101.5, 99.8, 102.3, 103.1, 102.0, 104.6, 105.2, 103.9, 106.4,
    107.0, 105.5, 108.2, 109.9, 108.1, 110.4, 111.8, 110.2, 112.5, 113.0,
    111.4, 114.2, 115.6, 113.8, 116.9, 118.0, 116.2, 119.4, 120.1, 118.7,
    121.6, 122.9, 121.0, 124.3, 125.5, 123.8, 126.7, 127.2, 125.9, 128.8,
]


def assert_series_close(actual, expected):
    assert len(actual) == len(expected)

    for a, e in zip(actual, expected):
        if e is None or (isinstance(e, float) and math.isnan(e)):
            assert a is None
        else:
            assert a == pytest.approx(e, rel=1e-9)


def test_sma_matches_pandas():
    expected = pd.Series(CLOSES).rolling(20).mean().tolist()

    assert_series_close(indicators.sma(CLOSES, 20), expected)


def test_ema_matches_sma_seeded_definition():
    period = 10
    multiplier = 2 / (period + 1)
    value = sum(CLOSES[:period]) / period
    expected = [None] * (period - 1) + [value]

    for close in CLOSES[period:]:
        value = (close - value) * multiplier + value
        expected.append(value)

    assert_series_close(indicators.ema(CLOSES, period), expected)


def test_rsi_matches_wilder_reference():
    period = 14
    delta = pd.Series(CLOSES).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: alpha = 1/period, seeded with a simple mean.
    avg_gain = [None] * len(CLOSES)
    avg_loss = [None] * len(CLOSES)
    avg_gain[period] = gain[1:period + 1].mean()
    avg_loss[period] = loss[1:period + 1].mean()

    for i in range(period + 1, len(CLOSES)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period

    expected = [
        None if g is None else 100 - 100 / (1 + g / l)
        for g, l in zip(avg_gain, avg_loss)
    ]

    assert_series_close(indicators.rsi(CLOSES, period), expected)


def test_rsi_bounds_for_monotonic_series():
    rising = [float(i) for i in range(1, 30)]
    flat = [5.0] * 30

    assert indicators.rsi(rising)[-1] == 100.0
    assert indicators.rsi(flat)[-1] == 50.0


def test_macd_histogram_is_line_minus_signal():
    line, signal, histogram = indicators.macd(CLOSES)

    assert line[24] is None
    assert line[25] is not None
    assert signal[32] is None
    assert signal[33] is not None
    assert histogram[-1] == pytest.approx(line[-1] - signal[-1])


def test_bollinger_matches_population_stdev():
    upper, middle, lower = indicators.bollinger_bands(CLOSES, 20, 2)
    series = pd.Series(CLOSES)
    mean = series.rolling(20).mean()
    std = series.rolling(20).std(ddof=0)

    assert_series_close(middle, mean.tolist())
    assert_series_close(upper, (mean + 2 * std).tolist())
    assert_series_close(lower, (mean - 2 * std).tolist())


def test_annualized_volatility_matches_pandas():
    expected = (
        pd.Series(CLOSES).pct_change().dropna().std() * math.sqrt(252)
    )

    assert indicators.annualized_volatility(CLOSES) == pytest.approx(expected)
    assert indicators.annualized_volatility([100.0, 101.0]) is None


def test_period_return():
    assert indicators.period_return(CLOSES, 5) == pytest.approx(
        CLOSES[-1] / CLOSES[-6] - 1
    )
    assert indicators.period_return(CLOSES, len(CLOSES)) is None


def test_short_history_returns_all_none():
    assert indicators.sma([1.0, 2.0], 5) == [None, None]
    assert indicators.ema([1.0, 2.0], 5) == [None, None]
    assert indicators.rsi([1.0, 2.0], 14) == [None, None]


def test_invalid_period_raises():
    with pytest.raises(ValueError):
        indicators.sma(CLOSES, 0)
