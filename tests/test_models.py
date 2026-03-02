"""Tests for data models."""

from __future__ import annotations

from datetime import date, datetime

from japan_finance_factors._models import (
    FactorCategory,
    FactorObservation,
    FactorResult,
    FinancialData,
    MonetaryUnit,
    PriceData,
)


class TestFinancialData:
    def test_from_dict(self) -> None:
        data = {"revenue": 100_000, "net_income": 10_000, "ticker": "7203"}
        fd = FinancialData.from_dict(data)
        assert fd.revenue == 100_000
        assert fd.net_income == 10_000
        assert fd.ticker == "7203"

    def test_from_dict_ignores_unknown(self) -> None:
        data = {"revenue": 100_000, "unknown_field": 42}
        fd = FinancialData.from_dict(data)
        assert fd.revenue == 100_000

    def test_normalized_jpy_noop(self) -> None:
        fd = FinancialData(revenue=100, unit=MonetaryUnit.JPY)
        assert fd.normalized() is fd

    def test_normalized_thousand_jpy(self) -> None:
        fd = FinancialData(
            revenue=1000,
            net_income=100,
            total_assets=5000,
            unit=MonetaryUnit.THOUSAND_JPY,
        )
        n = fd.normalized()
        assert n.unit == MonetaryUnit.JPY
        assert n.revenue == 1_000_000
        assert n.net_income == 100_000
        assert n.total_assets == 5_000_000

    def test_normalized_preserves_non_monetary(self) -> None:
        fd = FinancialData(
            ticker="7203",
            edinet_code="E02144",
            period_end=date(2025, 3, 31),
            revenue=1000,
            unit=MonetaryUnit.THOUSAND_JPY,
        )
        n = fd.normalized()
        assert n.ticker == "7203"
        assert n.edinet_code == "E02144"
        assert n.period_end == date(2025, 3, 31)

    def test_normalized_none_fields(self) -> None:
        fd = FinancialData(
            revenue=1000,
            net_income=None,
            unit=MonetaryUnit.THOUSAND_JPY,
        )
        n = fd.normalized()
        assert n.revenue == 1_000_000
        assert n.net_income is None

    def test_normalized_market_cap_not_multiplied(self) -> None:
        """market_cap and shares_outstanding are NOT monetary."""
        fd = FinancialData(
            revenue=1000,
            market_cap=50_000_000,
            shares_outstanding=1_000_000,
            unit=MonetaryUnit.THOUSAND_JPY,
        )
        n = fd.normalized()
        assert n.revenue == 1_000_000  # multiplied
        assert n.market_cap == 50_000_000  # NOT multiplied
        assert n.shares_outstanding == 1_000_000  # NOT multiplied


class TestPriceData:
    def test_closes(self) -> None:
        pd = PriceData(
            ticker="7203",
            prices=[
                {"date": "2025-01-01", "close": 100.0},
                {"date": "2025-01-02", "close": 102.0},
            ],
        )
        assert pd.closes() == [100.0, 102.0]

    def test_dates(self) -> None:
        pd = PriceData(
            ticker="7203",
            prices=[
                {"date": "2025-01-01", "close": 100.0},
                {"date": date(2025, 1, 2), "close": 102.0},
            ],
        )
        assert pd.dates() == [date(2025, 1, 1), date(2025, 1, 2)]

    def test_empty(self) -> None:
        pd = PriceData(ticker="7203")
        assert pd.closes() == []
        assert pd.dates() == []

    def test_unsorted_prices_sorted_by_closes(self) -> None:
        """Prices passed out-of-order should be sorted by date."""
        pd = PriceData(
            ticker="TEST",
            prices=[
                {"date": "2025-01-03", "close": 103.0},
                {"date": "2025-01-01", "close": 100.0},
                {"date": "2025-01-02", "close": 102.0},
            ],
        )
        assert pd.closes() == [100.0, 102.0, 103.0]
        assert pd.dates() == [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]


class TestFactorResult:
    def test_get(self) -> None:
        result = FactorResult(
            ticker="7203",
            as_of=datetime(2025, 7, 1),
            observations=[
                FactorObservation(
                    factor_id="ev_ebitda",
                    category=FactorCategory.VALUE,
                    value=8.5,
                    ticker="7203",
                    as_of=datetime(2025, 7, 1),
                ),
            ],
        )
        assert result.get("ev_ebitda") == 8.5
        assert result.get("nonexistent") is None

    def test_to_dict(self) -> None:
        result = FactorResult(
            ticker="7203",
            as_of=datetime(2025, 7, 1),
            observations=[
                FactorObservation(
                    factor_id="ev_ebitda",
                    category=FactorCategory.VALUE,
                    value=8.5,
                    ticker="7203",
                    as_of=datetime(2025, 7, 1),
                ),
                FactorObservation(
                    factor_id="fcf_yield",
                    category=FactorCategory.VALUE,
                    value=0.054,
                    ticker="7203",
                    as_of=datetime(2025, 7, 1),
                ),
            ],
        )
        d = result.to_dict()
        assert d == {"ev_ebitda": 8.5, "fcf_yield": 0.054}

    def test_frozen_observation(self) -> None:
        obs = FactorObservation(
            factor_id="ev_ebitda",
            category=FactorCategory.VALUE,
            value=8.5,
            ticker="7203",
            as_of=datetime(2025, 7, 1),
        )
        try:
            obs.value = 9.0  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass
