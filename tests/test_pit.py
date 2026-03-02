"""Tests for PIT alignment."""

from __future__ import annotations

from datetime import date, datetime

from japan_finance_factors._models import FinancialData, PriceData
from japan_finance_factors.pit.alignment import (
    filter_prices,
    is_available,
    select_financial_data,
    staleness_days,
)


class TestIsAvailable:
    def test_available(self) -> None:
        assert is_available(datetime(2025, 1, 1), datetime(2025, 6, 1))

    def test_not_available(self) -> None:
        assert not is_available(datetime(2025, 6, 1), datetime(2025, 1, 1))

    def test_exact_boundary(self) -> None:
        t = datetime(2025, 3, 15, 12, 0)
        assert is_available(t, t)

    def test_none_published_at(self) -> None:
        assert is_available(None, datetime(2025, 6, 1))


class TestFilterPrices:
    def test_filters_future_prices(self) -> None:
        pd = PriceData(
            ticker="TEST",
            prices=[
                {"date": "2025-01-01", "close": 100},
                {"date": "2025-03-01", "close": 110},
                {"date": "2025-06-01", "close": 120},
            ],
        )
        filtered = filter_prices(pd, datetime(2025, 4, 1))
        assert len(filtered.prices) == 2
        assert filtered.prices[-1]["close"] == 110

    def test_all_included(self) -> None:
        pd = PriceData(
            ticker="TEST",
            prices=[
                {"date": "2025-01-01", "close": 100},
                {"date": "2025-02-01", "close": 110},
            ],
        )
        filtered = filter_prices(pd, datetime(2025, 12, 31))
        assert len(filtered.prices) == 2

    def test_empty(self) -> None:
        pd = PriceData(ticker="TEST")
        filtered = filter_prices(pd, datetime(2025, 1, 1))
        assert len(filtered.prices) == 0

    def test_date_objects(self) -> None:
        pd = PriceData(
            ticker="TEST",
            prices=[
                {"date": date(2025, 1, 1), "close": 100},
                {"date": date(2025, 6, 1), "close": 120},
            ],
        )
        filtered = filter_prices(pd, datetime(2025, 3, 1))
        assert len(filtered.prices) == 1


class TestStaleness:
    def test_basic(self) -> None:
        assert staleness_days(datetime(2025, 1, 1), datetime(2025, 1, 11)) == 10

    def test_same_day(self) -> None:
        assert staleness_days(datetime(2025, 1, 1), datetime(2025, 1, 1)) == 0

    def test_none(self) -> None:
        assert staleness_days(None, datetime(2025, 1, 1)) is None


class TestSelectFinancialData:
    def test_selects_most_recent(self) -> None:
        candidates = [
            FinancialData(
                period_end=date(2024, 3, 31),
                published_at=datetime(2024, 6, 25),
                revenue=1000,
            ),
            FinancialData(
                period_end=date(2025, 3, 31),
                published_at=datetime(2025, 6, 25),
                revenue=1200,
            ),
        ]
        result = select_financial_data(candidates, datetime(2025, 7, 1))
        assert result is not None
        assert result.revenue == 1200

    def test_respects_as_of(self) -> None:
        candidates = [
            FinancialData(
                period_end=date(2024, 3, 31),
                published_at=datetime(2024, 6, 25),
                revenue=1000,
            ),
            FinancialData(
                period_end=date(2025, 3, 31),
                published_at=datetime(2025, 6, 25),
                revenue=1200,
            ),
        ]
        # as_of before the 2025 filing date
        result = select_financial_data(candidates, datetime(2025, 5, 1))
        assert result is not None
        assert result.revenue == 1000  # Only 2024 data available

    def test_empty_candidates(self) -> None:
        assert select_financial_data([], datetime(2025, 1, 1)) is None

    def test_none_available(self) -> None:
        candidates = [
            FinancialData(
                published_at=datetime(2026, 1, 1),
                revenue=1000,
            ),
        ]
        result = select_financial_data(candidates, datetime(2025, 1, 1))
        assert result is None
