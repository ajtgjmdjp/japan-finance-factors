"""Tests for the main compute_factors API."""

from __future__ import annotations

from datetime import datetime

from japan_finance_factors._models import FactorCategory, FinancialData, PriceData
from japan_finance_factors.api import ALL_FACTOR_IDS, compute_factors


class TestComputeFactors:
    def test_all_factors(
        self,
        toyota_financials: FinancialData,
        price_series_300d: PriceData,
    ) -> None:
        result = compute_factors(
            financial_data=toyota_financials,
            price_data=price_series_300d,
            as_of=datetime(2025, 7, 1),
        )
        assert result.ticker == "7203"
        assert len(result.observations) == len(ALL_FACTOR_IDS)

        d = result.to_dict()
        # Value factors
        assert d["ev_ebitda"] is not None
        assert d["fcf_yield"] is not None
        assert d["earnings_yield"] is not None
        assert d["book_to_market"] is not None
        # Quality factors
        assert d["piotroski_f_score"] is not None
        assert d["accruals_ratio"] is not None
        assert d["roe"] is not None
        assert d["roa"] is not None
        assert d["gross_margin"] is not None
        assert d["operating_margin"] is not None
        assert d["net_margin"] is not None
        assert d["debt_to_equity"] is not None
        assert d["current_ratio"] is not None
        # Size factors
        assert d["log_market_cap"] is not None
        # Momentum factors (depends on data length)
        assert "mom_3m" in d
        assert "mom_12m" in d
        # Risk factors
        assert "realized_vol_60d" in d
        assert "max_drawdown_252d" in d

    def test_financial_only(self, toyota_financials: FinancialData) -> None:
        result = compute_factors(
            financial_data=toyota_financials,
            as_of=datetime(2025, 7, 1),
        )
        assert len(result.observations) == 14  # 4 value + 9 quality + 1 size

    def test_price_only(self, price_series_300d: PriceData) -> None:
        result = compute_factors(
            price_data=price_series_300d,
            as_of=datetime(2025, 7, 1),
        )
        assert len(result.observations) == 4  # 2 momentum + 2 risk

    def test_selective_factors(self, toyota_financials: FinancialData) -> None:
        result = compute_factors(
            financial_data=toyota_financials,
            as_of=datetime(2025, 7, 1),
            factors=["ev_ebitda", "earnings_yield"],
        )
        assert len(result.observations) == 2
        ids = {o.factor_id for o in result.observations}
        assert ids == {"ev_ebitda", "earnings_yield"}

    def test_pit_metadata(self, toyota_financials: FinancialData) -> None:
        as_of = datetime(2025, 7, 1)
        result = compute_factors(
            financial_data=toyota_financials,
            as_of=as_of,
        )
        for obs in result.observations:
            assert obs.as_of == as_of
            assert obs.source_published_at == datetime(2025, 6, 25)
            assert obs.staleness_days == 6

    def test_category_assignment(self, toyota_financials: FinancialData) -> None:
        result = compute_factors(
            financial_data=toyota_financials,
            as_of=datetime(2025, 7, 1),
        )
        categories = {o.factor_id: o.category for o in result.observations}
        assert categories["ev_ebitda"] == FactorCategory.VALUE
        assert categories["piotroski_f_score"] == FactorCategory.QUALITY
        assert categories["log_market_cap"] == FactorCategory.SIZE

    def test_thousand_jpy_normalization(self) -> None:
        """Financial data in 千円 should be auto-normalized.

        market_cap is NOT multiplied (it's from market data, always JPY).
        """
        from japan_finance_factors._models import MonetaryUnit

        fd = FinancialData(
            ticker="TEST",
            revenue=45_000_000_000,  # 千円 → 45T JPY
            net_income=2_800_000_000,  # 千円 → 2.8T JPY
            operating_income=3_500_000_000,
            total_assets=90_000_000_000,
            operating_cf=4_500_000_000,
            market_cap=50_000_000_000_000,  # JPY (NOT multiplied)
            unit=MonetaryUnit.THOUSAND_JPY,
        )
        result = compute_factors(
            financial_data=fd,
            as_of=datetime(2025, 7, 1),
            factors=["earnings_yield"],
        )
        ey = result.get("earnings_yield")
        assert ey is not None
        # net_income = 2.8T, market_cap = 50T (unchanged)
        assert abs(ey - 0.056) < 0.001

    def test_financial_pit_lookahead_blocked(self) -> None:
        """Financial data not yet published at as_of should be blocked."""
        fd = FinancialData(
            ticker="TEST",
            revenue=1000,
            net_income=100,
            market_cap=2000,
            published_at=datetime(2025, 8, 1),  # Published AFTER as_of
        )
        result = compute_factors(
            financial_data=fd,
            as_of=datetime(2025, 7, 1),
            factors=["earnings_yield"],
        )
        # Should have no financial observations (PIT blocked)
        assert len(result.observations) == 0

    def test_unknown_factor_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown factor IDs"):
            compute_factors(
                as_of=datetime(2025, 7, 1),
                factors=["nonexistent_factor"],
            )

    def test_price_pit_filtering(self) -> None:
        """Prices after as_of should be excluded."""
        pd = PriceData(
            ticker="TEST",
            prices=[
                {"date": "2025-01-01", "close": 100},
                {"date": "2025-02-01", "close": 110},
                {"date": "2025-03-01", "close": 120},
                {"date": "2025-04-01", "close": 130},
                {"date": "2025-05-01", "close": 140},
            ],
        )
        result = compute_factors(
            price_data=pd,
            as_of=datetime(2025, 3, 15),
            factors=["mom_3m"],
        )
        # Should only use prices up to 2025-03-01
        # With only 3 data points, mom_3m needs 64, so result should be None
        assert result.get("mom_3m") is None
