"""Data models for factor calculation."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FactorCategory(str, Enum):
    """Factor category classification."""

    VALUE = "value"
    MOMENTUM = "momentum"
    QUALITY = "quality"
    RISK = "risk"
    SIZE = "size"


class MonetaryUnit(str, Enum):
    """Monetary value unit."""

    JPY = "jpy"
    THOUSAND_JPY = "thousand_jpy"


class FactorObservation(BaseModel):
    """A single factor value with PIT metadata."""

    factor_id: str
    category: FactorCategory
    value: float | None
    ticker: str
    as_of: datetime
    source_published_at: datetime | None = None
    source_period_end: date | None = None
    staleness_days: int | None = None

    model_config = {"frozen": True}


class FactorResult(BaseModel):
    """Collection of factor observations for one computation."""

    ticker: str
    as_of: datetime
    observations: list[FactorObservation] = Field(default_factory=list)

    def get(self, factor_id: str) -> float | None:
        """Get a factor value by ID."""
        for obs in self.observations:
            if obs.factor_id == factor_id:
                return obs.value
        return None

    def to_dict(self) -> dict[str, float | None]:
        """Convert to {factor_id: value} dict."""
        return {obs.factor_id: obs.value for obs in self.observations}


class FinancialData(BaseModel):
    """Normalized financial statement data for factor calculation.

    All monetary values must be in JPY (not thousands).
    Use ``FinancialData.from_edinet()`` or pass pre-normalized data.
    """

    ticker: str | None = None
    edinet_code: str | None = None
    period_end: date | None = None
    published_at: datetime | None = None

    # Income statement
    revenue: float | None = None
    cost_of_sales: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    ordinary_income: float | None = None
    net_income: float | None = None
    depreciation: float | None = None
    interest_expense: float | None = None

    # Balance sheet
    total_assets: float | None = None
    total_assets_prev: float | None = None
    current_assets: float | None = None
    cash_and_deposits: float | None = None
    receivables: float | None = None
    inventories: float | None = None
    total_liabilities: float | None = None
    current_liabilities: float | None = None
    short_term_debt: float | None = None
    long_term_debt: float | None = None
    total_equity: float | None = None
    total_equity_prev: float | None = None
    retained_earnings: float | None = None
    retained_earnings_prev: float | None = None

    # Cash flow
    operating_cf: float | None = None
    investing_cf: float | None = None
    capex: float | None = None

    # Per-share / market (NOT monetary — always in raw units)
    shares_outstanding: float | None = None
    shares_outstanding_prev: float | None = None
    market_cap: float | None = None

    # Previous period (for quality factors)
    revenue_prev: float | None = None
    gross_profit_prev: float | None = None
    operating_income_prev: float | None = None
    net_income_prev: float | None = None
    operating_cf_prev: float | None = None
    current_assets_prev: float | None = None
    current_liabilities_prev: float | None = None
    long_term_debt_prev: float | None = None

    # Metadata
    unit: MonetaryUnit = MonetaryUnit.JPY

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        unit: MonetaryUnit = MonetaryUnit.JPY,
    ) -> FinancialData:
        """Create from a flat dictionary with optional unit specification."""
        return cls(unit=unit, **{k: v for k, v in data.items() if k in cls.model_fields})

    # Fields that represent monetary amounts in statement units (千円 or 円).
    # shares_outstanding and market_cap are NOT monetary — they come from
    # market data and are always in raw units (shares / JPY respectively).
    _MONETARY_FIELDS: frozenset[str] = frozenset({
        "revenue", "cost_of_sales", "gross_profit", "operating_income",
        "ordinary_income", "net_income", "depreciation", "interest_expense",
        "total_assets", "total_assets_prev", "current_assets",
        "cash_and_deposits", "receivables", "inventories",
        "total_liabilities", "current_liabilities", "short_term_debt",
        "long_term_debt", "total_equity", "total_equity_prev",
        "retained_earnings", "retained_earnings_prev",
        "operating_cf", "investing_cf", "capex",
        "revenue_prev", "gross_profit_prev", "operating_income_prev",
        "net_income_prev", "operating_cf_prev",
        "current_assets_prev", "current_liabilities_prev",
        "long_term_debt_prev",
    })

    def normalized(self) -> FinancialData:
        """Return a copy with all monetary values converted to JPY.

        Only fields in ``_MONETARY_FIELDS`` are multiplied.
        ``shares_outstanding`` and ``market_cap`` are left unchanged
        because they originate from market data, not financial statements.
        """
        if self.unit == MonetaryUnit.JPY:
            return self
        multiplier = 1000.0 if self.unit == MonetaryUnit.THOUSAND_JPY else 1.0
        updates: dict[str, Any] = {"unit": MonetaryUnit.JPY}
        for field_name in self._MONETARY_FIELDS:
            val = getattr(self, field_name)
            if val is not None:
                updates[field_name] = val * multiplier
        return self.model_copy(update=updates)


class PriceData(BaseModel):
    """Price time series for a single ticker.

    ``prices`` is a list of dicts with at least ``date`` and ``close`` keys.
    Sorted by date ascending.
    """

    ticker: str
    prices: list[dict[str, Any]] = Field(default_factory=list)
    market_cap: float | None = None
    shares_outstanding: float | None = None

    def _sorted_prices(self) -> list[dict[str, Any]]:
        """Return prices sorted by date ascending."""
        def _parse_date(p: dict[str, Any]) -> date:
            d = p.get("date")
            if isinstance(d, date) and not isinstance(d, datetime):
                return d
            if isinstance(d, datetime):
                return d.date()
            if isinstance(d, str):
                return date.fromisoformat(d)
            return date.min
        return sorted(self.prices, key=_parse_date)

    def closes(self) -> list[float]:
        """Extract close prices sorted by date ascending."""
        return [
            float(p["close"])
            for p in self._sorted_prices()
            if p.get("close") is not None
        ]

    def dates(self) -> list[date]:
        """Extract dates sorted ascending."""
        result: list[date] = []
        for p in self._sorted_prices():
            d = p.get("date")
            if isinstance(d, date) and not isinstance(d, datetime):
                result.append(d)
            elif isinstance(d, datetime):
                result.append(d.date())
            elif isinstance(d, str):
                result.append(date.fromisoformat(d))
        return result
