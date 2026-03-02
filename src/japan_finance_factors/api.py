"""Public API for factor computation."""

from __future__ import annotations

from datetime import datetime

from japan_finance_factors._models import (
    FactorCategory,
    FactorObservation,
    FactorResult,
    FinancialData,
    PriceData,
)
from japan_finance_factors.factors import momentum, quality, risk, value
from japan_finance_factors.pit.alignment import (
    filter_prices,
    is_available,
    staleness_days,
)

# Factor registry: (factor_id, category, callable, input_type)
_FINANCIAL_FACTORS: list[tuple[str, FactorCategory, object]] = [
    ("ev_ebitda", FactorCategory.VALUE, value.ev_ebitda),
    ("fcf_yield", FactorCategory.VALUE, value.fcf_yield),
    ("earnings_yield", FactorCategory.VALUE, value.earnings_yield),
    ("book_to_market", FactorCategory.VALUE, value.book_to_market),
    ("piotroski_f_score", FactorCategory.QUALITY, quality.piotroski_f_score),
    ("accruals_ratio", FactorCategory.QUALITY, quality.accruals_ratio),
]

_PRICE_FACTORS: list[tuple[str, FactorCategory, object]] = [
    ("mom_3m", FactorCategory.MOMENTUM, momentum.mom_3m),
    ("mom_12m", FactorCategory.MOMENTUM, momentum.mom_12m),
    ("realized_vol_60d", FactorCategory.RISK, risk.realized_vol_60d),
    ("max_drawdown_252d", FactorCategory.RISK, risk.max_drawdown_252d),
]

ALL_FACTOR_IDS = [f[0] for f in _FINANCIAL_FACTORS + _PRICE_FACTORS]
_ALL_FACTOR_ID_SET = frozenset(ALL_FACTOR_IDS)


def compute_factors(
    *,
    financial_data: FinancialData | None = None,
    price_data: PriceData | None = None,
    as_of: datetime,
    factors: list[str] | None = None,
) -> FactorResult:
    """Compute quantitative factors for a single ticker.

    Args:
        financial_data: Normalized financial statement data.
            Must be in JPY units (use ``FinancialData.normalized()``
            if data is in thousands).
        price_data: Price time series data.
        as_of: Point-in-time cutoff. Only data published before this
            timestamp is used. Financial data with ``published_at > as_of``
            is rejected to prevent lookahead bias.
        factors: List of factor IDs to compute. If None, computes all
            available factors.

    Returns:
        FactorResult containing all computed factor observations.

    Raises:
        ValueError: If unknown factor IDs are requested.
    """
    # Validate requested factor IDs
    if factors is not None:
        unknown = set(factors) - _ALL_FACTOR_ID_SET
        if unknown:
            raise ValueError(f"Unknown factor IDs: {sorted(unknown)}")

    ticker = ""
    if financial_data is not None:
        ticker = financial_data.ticker or ""
    elif price_data is not None:
        ticker = price_data.ticker

    requested = set(factors) if factors else None
    observations: list[FactorObservation] = []

    # Normalize financial data if needed, with PIT guard
    fd = None
    if financial_data is not None:
        if not is_available(financial_data.published_at, as_of):
            # Financial data not yet published at as_of → skip to prevent lookahead
            fd = None
        else:
            fd = financial_data.normalized()

    # Filter prices to as_of cutoff
    pd = None
    if price_data is not None:
        pd = filter_prices(price_data, as_of)

    # Compute financial-based factors
    if fd is not None:
        stale = staleness_days(fd.published_at, as_of)
        for factor_id, category, func in _FINANCIAL_FACTORS:
            if requested is not None and factor_id not in requested:
                continue
            val = func(fd)  # type: ignore[operator]
            observations.append(
                FactorObservation(
                    factor_id=factor_id,
                    category=category,
                    value=val,
                    ticker=ticker,
                    as_of=as_of,
                    source_published_at=fd.published_at,
                    source_period_end=fd.period_end,
                    staleness_days=stale,
                )
            )

    # Compute price-based factors
    if pd is not None:
        for factor_id, category, func in _PRICE_FACTORS:
            if requested is not None and factor_id not in requested:
                continue
            val = func(pd)  # type: ignore[operator]
            observations.append(
                FactorObservation(
                    factor_id=factor_id,
                    category=category,
                    value=val,
                    ticker=ticker or pd.ticker,
                    as_of=as_of,
                    source_published_at=None,
                    source_period_end=None,
                    staleness_days=None,
                )
            )

    return FactorResult(
        ticker=ticker or (pd.ticker if pd else ""),
        as_of=as_of,
        observations=observations,
    )
