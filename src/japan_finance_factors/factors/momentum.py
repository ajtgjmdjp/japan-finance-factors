"""Momentum factor calculations.

Functions accept price series and return momentum values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import PriceData

# Approximate trading days per period
_TRADING_DAYS_1M = 21
_TRADING_DAYS_3M = 63
_TRADING_DAYS_12M = 252


def _price_return(closes: list[float], lookback_days: int) -> float | None:
    """Calculate simple return over a lookback period.

    Args:
        closes: Close prices sorted by date ascending.
        lookback_days: Number of trading days to look back.

    Returns:
        Simple return (e.g., 0.05 for 5% gain), or None if insufficient data.
    """
    if len(closes) < lookback_days + 1:
        return None
    current = closes[-1]
    past = closes[-(lookback_days + 1)]
    if past == 0:
        return None
    return (current - past) / past


def mom_3m(price_data: PriceData) -> float | None:
    """3-month price momentum (approximately 63 trading days)."""
    return _price_return(price_data.closes(), _TRADING_DAYS_3M)


def mom_12m(price_data: PriceData) -> float | None:
    """12-month price momentum (approximately 252 trading days).

    Uses the standard 12-1 convention: returns over the past 12 months
    excluding the most recent month, to avoid short-term reversal effects.
    """
    closes = price_data.closes()
    # Need at least 252 + 1 data points
    if len(closes) < _TRADING_DAYS_12M + 1:
        return None
    # Skip the most recent month (21 days)
    end_idx = len(closes) - _TRADING_DAYS_1M
    start_idx = end_idx - (_TRADING_DAYS_12M - _TRADING_DAYS_1M)
    if start_idx < 0:
        return None
    past = closes[start_idx]
    current = closes[end_idx - 1]
    if past == 0:
        return None
    return (current - past) / past
