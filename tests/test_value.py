"""Tests for value factor calculations."""

from __future__ import annotations

from japan_finance_factors._models import FinancialData
from japan_finance_factors.factors.value import (
    book_to_market,
    earnings_yield,
    ev_ebitda,
    fcf_yield,
)


class TestEvEbitda:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = ev_ebitda(toyota_financials)
        assert result is not None
        # EV = 50T + (3T + 15T) - 8T = 60T
        # EBITDA = 3.5T + 1.2T = 4.7T
        # EV/EBITDA = 60T / 4.7T ≈ 12.77
        assert 12.0 < result < 13.5

    def test_no_market_cap(self) -> None:
        fd = FinancialData(operating_income=1_000_000)
        assert ev_ebitda(fd) is None

    def test_no_operating_income(self) -> None:
        fd = FinancialData(market_cap=1_000_000_000)
        assert ev_ebitda(fd) is None

    def test_zero_ebitda(self) -> None:
        fd = FinancialData(
            market_cap=1_000_000_000,
            operating_income=0,
            depreciation=0,
        )
        assert ev_ebitda(fd) is None

    def test_no_debt_no_cash(self) -> None:
        fd = FinancialData(
            market_cap=1_000_000_000,
            operating_income=100_000_000,
            depreciation=50_000_000,
        )
        result = ev_ebitda(fd)
        assert result is not None
        # EV = 1B + 0 - 0 = 1B, EBITDA = 150M
        assert abs(result - 1_000_000_000 / 150_000_000) < 0.01


class TestFcfYield:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = fcf_yield(toyota_financials)
        assert result is not None
        # FCF = 4.5T - 1.8T = 2.7T, market_cap = 50T
        # FCF yield = 2.7T / 50T = 0.054
        assert abs(result - 0.054) < 0.001

    def test_no_operating_cf(self) -> None:
        fd = FinancialData(market_cap=1_000_000_000)
        assert fcf_yield(fd) is None

    def test_negative_fcf(self) -> None:
        fd = FinancialData(
            market_cap=1_000_000_000,
            operating_cf=100_000_000,
            capex=-500_000_000,
        )
        result = fcf_yield(fd)
        assert result is not None
        assert result < 0  # Negative FCF


class TestEarningsYield:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = earnings_yield(toyota_financials)
        assert result is not None
        # 2.8T / 50T = 0.056
        assert abs(result - 0.056) < 0.001

    def test_no_net_income(self) -> None:
        fd = FinancialData(market_cap=1_000_000_000)
        assert earnings_yield(fd) is None


class TestBookToMarket:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = book_to_market(toyota_financials)
        assert result is not None
        # 35T / 50T = 0.7
        assert abs(result - 0.7) < 0.01

    def test_no_equity(self) -> None:
        fd = FinancialData(market_cap=1_000_000_000)
        assert book_to_market(fd) is None
