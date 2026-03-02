"""Shared test fixtures."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from japan_finance_factors._models import FinancialData, PriceData


@pytest.fixture()
def toyota_financials() -> FinancialData:
    """Realistic Toyota-like financial data (JPY units)."""
    return FinancialData(
        ticker="7203",
        edinet_code="E02144",
        period_end=date(2025, 3, 31),
        published_at=datetime(2025, 6, 25),
        # Income statement (JPY)
        revenue=45_000_000_000_000,
        cost_of_sales=37_000_000_000_000,
        gross_profit=8_000_000_000_000,
        operating_income=3_500_000_000_000,
        ordinary_income=4_000_000_000_000,
        net_income=2_800_000_000_000,
        depreciation=1_200_000_000_000,
        interest_expense=100_000_000_000,
        # Balance sheet
        total_assets=90_000_000_000_000,
        total_assets_prev=85_000_000_000_000,
        current_assets=25_000_000_000_000,
        cash_and_deposits=8_000_000_000_000,
        receivables=5_000_000_000_000,
        inventories=4_000_000_000_000,
        total_liabilities=55_000_000_000_000,
        current_liabilities=20_000_000_000_000,
        short_term_debt=3_000_000_000_000,
        long_term_debt=15_000_000_000_000,
        total_equity=35_000_000_000_000,
        total_equity_prev=33_000_000_000_000,
        retained_earnings=28_000_000_000_000,
        retained_earnings_prev=26_000_000_000_000,
        # Cash flow
        operating_cf=4_500_000_000_000,
        investing_cf=-2_000_000_000_000,
        capex=-1_800_000_000_000,
        # Market
        shares_outstanding=14_000_000_000,
        market_cap=50_000_000_000_000,
        # Previous period
        revenue_prev=42_000_000_000_000,
        gross_profit_prev=7_500_000_000_000,
        operating_income_prev=3_200_000_000_000,
        net_income_prev=2_500_000_000_000,
        operating_cf_prev=4_000_000_000_000,
        current_assets_prev=23_000_000_000_000,
        current_liabilities_prev=19_000_000_000_000,
        long_term_debt_prev=16_000_000_000_000,
    )


@pytest.fixture()
def price_series_300d() -> PriceData:
    """300 days of synthetic price data with uptrend + drawdown."""
    prices = []
    base_price = 2000.0
    for i in range(300):
        d = date(2024, 1, 2)
        try:
            from datetime import timedelta

            d = date(2024, 1, 2) + timedelta(days=i)
        except Exception:
            pass
        # Uptrend for first 200 days, then 20% drawdown, then recovery
        if i < 200:
            price = base_price * (1 + 0.0005 * i)  # ~10% over 200 days
        elif i < 240:
            price = base_price * 1.10 * (1 - 0.005 * (i - 200))  # drawdown
        else:
            price = base_price * 1.10 * 0.80 * (1 + 0.002 * (i - 240))  # recovery
        prices.append({
            "date": d.isoformat(),
            "close": round(price, 1),
            "open": round(price * 0.999, 1),
            "high": round(price * 1.002, 1),
            "low": round(price * 0.998, 1),
            "volume": 1000000,
        })
    return PriceData(ticker="7203", prices=prices, market_cap=50_000_000_000_000)
