"""Tests for momentum factor calculations."""

from __future__ import annotations

from datetime import date, timedelta

from japan_finance_factors._models import PriceData
from japan_finance_factors.factors.momentum import mom_3m, mom_12m


def _make_prices(n: int, start_price: float = 100.0, step: float = 1.0) -> list[dict]:
    base = date(2024, 1, 1)
    return [
        {"date": (base + timedelta(days=i)).isoformat(), "close": start_price + step * i}
        for i in range(n)
    ]


class TestMom3m:
    def test_basic(self, price_series_300d: PriceData) -> None:
        result = mom_3m(price_series_300d)
        assert result is not None

    def test_positive_trend(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(100, step=1.0))
        result = mom_3m(pd)
        assert result is not None
        assert result > 0

    def test_negative_trend(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(100, start_price=200, step=-1.0))
        result = mom_3m(pd)
        assert result is not None
        assert result < 0

    def test_insufficient_data(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(30, step=0.0))
        assert mom_3m(pd) is None


class TestMom12m:
    def test_basic(self, price_series_300d: PriceData) -> None:
        result = mom_12m(price_series_300d)
        if len(price_series_300d.closes()) >= 253:
            assert result is not None

    def test_insufficient_data(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(200, step=0.0))
        assert mom_12m(pd) is None

    def test_long_series(self) -> None:
        """12-month momentum with 1 year+ of data."""
        pd = PriceData(ticker="TEST", prices=_make_prices(300, step=0.1))
        result = mom_12m(pd)
        if result is not None:
            assert result > 0
