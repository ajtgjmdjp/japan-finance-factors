"""Tests for risk factor calculations."""

from __future__ import annotations

import random
from datetime import date, timedelta

from japan_finance_factors._models import PriceData
from japan_finance_factors.factors.risk import max_drawdown_252d, realized_vol_60d


def _make_prices(n: int, start_price: float = 100.0, step: float = 0.0) -> list[dict]:
    base = date(2024, 1, 1)
    return [
        {"date": (base + timedelta(days=i)).isoformat(), "close": start_price + step * i}
        for i in range(n)
    ]


class TestRealizedVol60d:
    def test_basic(self, price_series_300d: PriceData) -> None:
        result = realized_vol_60d(price_series_300d)
        assert result is not None
        assert result > 0

    def test_constant_price(self) -> None:
        """Constant prices should have near-zero vol."""
        pd = PriceData(ticker="TEST", prices=_make_prices(100, step=0.0))
        result = realized_vol_60d(pd)
        assert result is not None
        assert result < 0.001

    def test_insufficient_data(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(30, step=0.0))
        assert realized_vol_60d(pd) is None

    def test_annualized(self) -> None:
        """Verify annualization factor is applied."""
        random.seed(42)
        base = date(2024, 1, 1)
        prices = [
            {
                "date": (base + timedelta(days=i)).isoformat(),
                "close": 100 + random.gauss(0, 1),
            }
            for i in range(100)
        ]
        pd = PriceData(ticker="TEST", prices=prices)
        result = realized_vol_60d(pd)
        assert result is not None
        assert result > 0.05


class TestMaxDrawdown252d:
    def test_basic(self, price_series_300d: PriceData) -> None:
        result = max_drawdown_252d(price_series_300d)
        assert result is not None
        assert result <= 0
        assert result < -0.10

    def test_no_drawdown(self) -> None:
        """Monotonically increasing prices have zero drawdown."""
        pd = PriceData(ticker="TEST", prices=_make_prices(260, step=1.0))
        result = max_drawdown_252d(pd)
        assert result is not None
        assert result == 0.0

    def test_full_drawdown(self) -> None:
        """Price drops to near zero."""
        base = date(2024, 1, 1)
        prices = [
            {
                "date": (base + timedelta(days=i)).isoformat(),
                "close": max(100 - 0.4 * i, 1.0),
            }
            for i in range(260)
        ]
        pd = PriceData(ticker="TEST", prices=prices)
        result = max_drawdown_252d(pd)
        assert result is not None
        assert result < -0.90

    def test_insufficient_data(self) -> None:
        pd = PriceData(ticker="TEST", prices=_make_prices(100, step=0.0))
        assert max_drawdown_252d(pd) is None
