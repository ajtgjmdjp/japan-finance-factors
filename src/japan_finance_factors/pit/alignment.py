"""Point-in-time alignment for factor calculation.

Ensures that factor calculations only use data that was publicly
available at the ``as_of`` timestamp, preventing lookahead bias.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import FinancialData, PriceData


def is_available(published_at: datetime | None, as_of: datetime) -> bool:
    """Check if a data point was published before the as_of cutoff."""
    if published_at is None:
        return True  # No publication date → assume available (user's responsibility)
    return published_at <= as_of


def filter_prices(price_data: PriceData, as_of: datetime) -> PriceData:
    """Filter price data to only include entries up to as_of date.

    Returns a new PriceData with prices trimmed to the cutoff.
    """
    cutoff = as_of.date() if isinstance(as_of, datetime) else as_of
    filtered = []
    for p in price_data.prices:
        d = p.get("date")
        if d is None:
            continue
        if isinstance(d, str):
            d = date.fromisoformat(d)
        if isinstance(d, datetime):
            d = d.date()
        if d <= cutoff:
            filtered.append(p)
    return price_data.model_copy(update={"prices": filtered})


def staleness_days(published_at: datetime | None, as_of: datetime) -> int | None:
    """Calculate how stale a data point is relative to as_of."""
    if published_at is None:
        return None
    delta = as_of - published_at
    return max(0, delta.days)


def select_financial_data(
    candidates: list[FinancialData],
    as_of: datetime,
) -> FinancialData | None:
    """Select the most recent financial data available at as_of.

    From a list of financial data snapshots, returns the one with the
    latest period_end that was published before as_of.
    """
    available = [
        fd for fd in candidates if is_available(fd.published_at, as_of)
    ]
    if not available:
        return None
    # Prefer the most recent period; break ties by latest publication
    return max(
        available,
        key=lambda fd: (fd.period_end or date.min, fd.published_at or datetime.min),
    )
