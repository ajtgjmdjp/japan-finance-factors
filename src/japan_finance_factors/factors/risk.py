"""Risk factor calculations.

Functions assess price-based risk metrics.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import PriceData

_TRADING_DAYS_60D = 60
_TRADING_DAYS_252D = 252
_ANNUALIZATION_FACTOR = math.sqrt(252)


def _daily_returns(closes: list[float]) -> list[float]:
    """Calculate daily simple returns from close prices."""
    if len(closes) < 2:
        return []
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]


def realized_vol_60d(price_data: PriceData) -> float | None:
    """60-day annualized realized volatility.

    Standard deviation of daily returns over the last 60 trading days,
    annualized by sqrt(252).
    """
    closes = price_data.closes()
    if len(closes) < _TRADING_DAYS_60D + 1:
        return None
    recent = closes[-(_TRADING_DAYS_60D + 1):]
    returns = _daily_returns(recent)
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * _ANNUALIZATION_FACTOR


def max_drawdown_252d(price_data: PriceData) -> float | None:
    """Maximum drawdown over the last 252 trading days.

    Returns a non-positive value (e.g., -0.25 for a 25% drawdown).
    Returns 0.0 if no drawdown occurred.
    """
    closes = price_data.closes()
    if len(closes) < _TRADING_DAYS_252D:
        return None
    recent = closes[-_TRADING_DAYS_252D:]
    peak = recent[0]
    max_dd = 0.0
    for price in recent:
        if price > peak:
            peak = price
        if peak > 0:
            dd = (price - peak) / peak
            if dd < max_dd:
                max_dd = dd
    return max_dd
