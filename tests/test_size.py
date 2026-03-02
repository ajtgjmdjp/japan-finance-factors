"""Tests for size factor calculations."""

from __future__ import annotations

import math

from japan_finance_factors._models import FinancialData
from japan_finance_factors.factors.size import log_market_cap


class TestLogMarketCap:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = log_market_cap(toyota_financials)
        assert result is not None
        # Toyota market_cap ≈ 50T JPY → log(50e12) ≈ 31.2
        assert 28 < result < 35

    def test_known_value(self) -> None:
        fd = FinancialData(market_cap=1_000_000_000_000)  # 1T JPY
        result = log_market_cap(fd)
        assert result is not None
        assert abs(result - math.log(1e12)) < 0.001

    def test_missing(self) -> None:
        fd = FinancialData()
        assert log_market_cap(fd) is None

    def test_zero(self) -> None:
        fd = FinancialData(market_cap=0)
        assert log_market_cap(fd) is None

    def test_negative(self) -> None:
        fd = FinancialData(market_cap=-100)
        assert log_market_cap(fd) is None
