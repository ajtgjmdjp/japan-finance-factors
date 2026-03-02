"""Tests for quality factor calculations."""

from __future__ import annotations

from japan_finance_factors._models import FinancialData
from japan_finance_factors.factors.quality import (
    accruals_ratio,
    current_ratio,
    debt_to_equity,
    gross_margin,
    net_margin,
    operating_margin,
    piotroski_f_score,
    roa,
    roe,
)


class TestPiotroskiFScore:
    def test_strong_company(self, toyota_financials: FinancialData) -> None:
        """Toyota-like financials should score high."""
        result = piotroski_f_score(toyota_financials)
        assert result is not None
        # Toyota fixture has:
        # F1: net_income > 0 ✓
        # F2: ROA > 0 ✓
        # F3: operating_cf > 0 ✓
        # F4: operating_cf > net_income ✓ (4.5T > 2.8T)
        # F5: leverage decreased ✓ (15T/87.5T < 16T/85T)
        # F6: current ratio increased ✓ (25/20=1.25 > 23/19=1.21)
        # F7: no dilution ✓ (default)
        # F8: gross margin increased ✓ (8/45 > 7.5/42)
        # F9: asset turnover increased ✓ (45/87.5 > 42/85)
        assert result >= 7

    def test_missing_critical_fields(self) -> None:
        fd = FinancialData()
        assert piotroski_f_score(fd) is None

    def test_weak_company(self) -> None:
        """Company with losses and deterioration."""
        fd = FinancialData(
            net_income=-100,
            total_assets=10000,
            total_assets_prev=9000,
            operating_cf=-50,
            long_term_debt=5000,
            long_term_debt_prev=4000,
            current_assets=2000,
            current_liabilities=3000,
            current_assets_prev=2500,
            current_liabilities_prev=2000,
            revenue=8000,
            revenue_prev=9000,
            gross_profit=1000,
            gross_profit_prev=1500,
        )
        result = piotroski_f_score(fd)
        assert result is not None
        assert result <= 3  # Weak score

    def test_score_range(self, toyota_financials: FinancialData) -> None:
        result = piotroski_f_score(toyota_financials)
        assert result is not None
        assert 0 <= result <= 9


class TestAccrualsRatio:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = accruals_ratio(toyota_financials)
        assert result is not None
        # (2.8T - 4.5T) / 90T = -0.0189
        assert abs(result - (-1_700_000_000_000 / 90_000_000_000_000)) < 0.001

    def test_negative_is_good(self, toyota_financials: FinancialData) -> None:
        """Negative accruals = cash flow exceeds earnings = higher quality."""
        result = accruals_ratio(toyota_financials)
        assert result is not None
        assert result < 0

    def test_positive_accruals(self) -> None:
        """Positive accruals = earnings exceed cash flow = lower quality."""
        fd = FinancialData(
            net_income=500,
            operating_cf=200,
            total_assets=10000,
        )
        result = accruals_ratio(fd)
        assert result is not None
        assert result > 0
        assert abs(result - 0.03) < 0.001

    def test_missing_fields(self) -> None:
        fd = FinancialData(net_income=100)
        assert accruals_ratio(fd) is None

    def test_zero_assets(self) -> None:
        fd = FinancialData(net_income=100, operating_cf=50, total_assets=0)
        assert accruals_ratio(fd) is None


class TestROE:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = roe(toyota_financials)
        assert result is not None
        assert 0 < result < 0.5

    def test_missing_equity(self) -> None:
        fd = FinancialData(net_income=100)
        assert roe(fd) is None

    def test_zero_equity(self) -> None:
        fd = FinancialData(net_income=100, total_equity=0)
        assert roe(fd) is None

    def test_negative_income(self) -> None:
        fd = FinancialData(net_income=-100, total_equity=1000)
        result = roe(fd)
        assert result is not None
        assert result < 0


class TestROA:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = roa(toyota_financials)
        assert result is not None
        assert 0 < result < 0.2

    def test_missing_assets(self) -> None:
        fd = FinancialData(net_income=100)
        assert roa(fd) is None


class TestGrossMargin:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = gross_margin(toyota_financials)
        assert result is not None
        assert 0 < result < 1

    def test_missing_fields(self) -> None:
        fd = FinancialData(revenue=1000)
        assert gross_margin(fd) is None

    def test_zero_revenue(self) -> None:
        fd = FinancialData(gross_profit=100, revenue=0)
        assert gross_margin(fd) is None


class TestOperatingMargin:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = operating_margin(toyota_financials)
        assert result is not None
        assert 0 < result < 1

    def test_missing_fields(self) -> None:
        fd = FinancialData(revenue=1000)
        assert operating_margin(fd) is None


class TestNetMargin:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = net_margin(toyota_financials)
        assert result is not None
        assert 0 < result < 1

    def test_negative(self) -> None:
        fd = FinancialData(net_income=-50, revenue=1000)
        result = net_margin(fd)
        assert result is not None
        assert result < 0


class TestDebtToEquity:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = debt_to_equity(toyota_financials)
        assert result is not None
        assert result > 0

    def test_missing_fields(self) -> None:
        fd = FinancialData(total_liabilities=100)
        assert debt_to_equity(fd) is None

    def test_zero_equity(self) -> None:
        fd = FinancialData(total_liabilities=100, total_equity=0)
        assert debt_to_equity(fd) is None


class TestCurrentRatio:
    def test_basic(self, toyota_financials: FinancialData) -> None:
        result = current_ratio(toyota_financials)
        assert result is not None
        assert result > 0

    def test_missing_fields(self) -> None:
        fd = FinancialData(current_assets=100)
        assert current_ratio(fd) is None

    def test_healthy(self) -> None:
        fd = FinancialData(current_assets=200, current_liabilities=100)
        result = current_ratio(fd)
        assert result is not None
        assert result == 2.0
