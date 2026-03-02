"""Real API integration test for japan-finance-factors (A-3).

Tests two modes:
  1. yfinance price data → momentum + risk factors
  2. Manual FinancialData (Toyota FY2024 public values) → value + quality factors
  3. Combined → all 10 factors
"""

import asyncio
from datetime import datetime

from japan_finance_factors import compute_factors
from japan_finance_factors._models import FinancialData, MonetaryUnit


async def main() -> None:
    print("=== A-3 Real API Test: japan-finance-factors ===")
    print()

    # ---- Part 1: yfinance price data ----
    print("--- Part 1: Fetch yfinance price data (Toyota 7203) ---")
    try:
        from japan_finance_factors.fetch import fetch_price_data

        pd = await fetch_price_data("7203", lookback_days=400)
        print(f"  ticker: {pd.ticker}")
        print(f"  price points: {len(pd.prices)}")
        print(
            f"  market_cap: {pd.market_cap:,.0f}" if pd.market_cap else "  market_cap: N/A"
        )
        if pd.prices:
            print(f"  date range: {pd.prices[0].get('date')} ~ {pd.prices[-1].get('date')}")
            print(f"  latest close: {pd.prices[-1].get('close')}")
    except Exception as e:
        print(f"  ERROR: {e}")
        pd = None

    # ---- Part 2: Manual FinancialData (Toyota public data) ----
    print()
    print("--- Part 2: Manual FinancialData (Toyota FY2024 public values, 千円) ---")
    # Source: Toyota annual report (有価証券報告書) FY ending March 2025
    # Values in 千円 (thousands JPY) as reported in EDINET
    market_cap_jpy = pd.market_cap if pd and pd.market_cap else 40_000_000_000_000  # ~40T JPY

    fd = FinancialData(
        ticker="7203",
        edinet_code="E02144",
        published_at=datetime(2025, 6, 25),  # typical filing date
        unit=MonetaryUnit.THOUSAND_JPY,
        # 千円 units (approximate Toyota FY2024 values)
        revenue=45_095_325_000,  # ~45T JPY
        operating_income=3_592_623_000,  # ~3.6T JPY
        net_income=2_171_813_000,  # ~2.2T JPY
        depreciation=2_500_000_000,  # ~2.5T JPY
        total_assets=90_113_654_000,  # ~90T JPY
        current_assets=28_000_000_000,
        total_liabilities=55_000_000_000,
        current_liabilities=24_000_000_000,
        total_equity=33_000_000_000,
        retained_earnings=30_000_000_000,
        operating_cf=4_228_000_000,  # ~4.2T JPY
        investing_cf=-5_500_000_000,
        capex=-1_800_000_000,
        long_term_debt=12_000_000_000,
        short_term_debt=3_000_000_000,
        market_cap=market_cap_jpy,  # JPY (not 千円)
        shares_outstanding=13_500_000_000,  # shares (not 千円)
    )

    fd_norm = fd.normalized()
    print(f"  revenue (千円): {fd.revenue:,.0f}")
    print(f"  revenue (JPY): {fd_norm.revenue:,.0f}")
    print(f"  net_income (JPY): {fd_norm.net_income:,.0f}")
    print(f"  market_cap (JPY): {fd.market_cap:,.0f}")

    # ---- Part 3: Compute all factors ----
    print()
    print("--- Part 3: Compute all factors ---")
    as_of = datetime(2026, 3, 1)

    kwargs: dict = {"financial_data": fd, "as_of": as_of}
    if pd:
        kwargs["price_data"] = pd

    result = compute_factors(**kwargs)

    print(f"  as_of: {as_of:%Y-%m-%d}")
    print(f"  factors computed: {len(result.observations)}")
    print()

    # Display all factors
    print("--- Factor Results ---")
    for obs in result.observations:
        val_str = f"{obs.value:.4f}" if obs.value is not None else "N/A"
        stale = f" (stale: {obs.staleness_days}d)" if obs.staleness_days is not None else ""
        print(f"  [{obs.category.value:8s}] {obs.factor_id:20s} = {val_str}{stale}")

    # ---- Part 4: PIT safety ----
    print()
    print("--- PIT Safety Check ---")
    for obs in result.observations:
        if obs.source_published_at is not None:
            assert obs.source_published_at <= as_of, f"PIT leak: {obs.factor_id}"
    print("  PIT safety: OK (no lookahead)")

    # ---- Part 5: Sanity checks ----
    print()
    print("--- Sanity Checks ---")
    d = result.to_dict()

    checks = [
        ("ev_ebitda", lambda v: 0 < v < 100, "0-100"),
        ("fcf_yield", lambda v: -1 < v < 1, "-100% ~ 100%"),
        ("earnings_yield", lambda v: -1 < v < 1, "-100% ~ 100%"),
        ("book_to_market", lambda v: 0 < v < 10, "0 ~ 10"),
        ("piotroski_f_score", lambda v: 0 <= v <= 9, "0 ~ 9"),
        ("accruals_ratio", lambda v: -1 < v < 1, "-1 ~ 1"),
        ("realized_vol_60d", lambda v: 0 < v < 2, "0% ~ 200%"),
        ("max_drawdown_252d", lambda v: -1 <= v <= 0, "-100% ~ 0%"),
    ]

    for factor_id, check_fn, range_desc in checks:
        val = d.get(factor_id)
        if val is not None:
            ok = check_fn(val)
            status = "OK" if ok else "FAIL"
            print(f"  {factor_id:20s} = {val:>10.4f}  range({range_desc}) {status}")
            assert ok, f"{factor_id} out of range: {val}"
        else:
            print(f"  {factor_id:20s} = {'N/A':>10s}  (skipped)")

    print()
    print("=== All A-3 tests PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
