"""Quality factor calculations.

Functions assess the quality and reliability of a company's financials.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import FinancialData


def piotroski_f_score(fd: FinancialData) -> float | None:
    """Piotroski F-Score (0-9).

    A composite score measuring financial strength across three dimensions:
    - Profitability (4 signals)
    - Leverage/Liquidity (3 signals)
    - Operating Efficiency (2 signals)

    Requires current and previous period data.
    Returns None if critical fields are missing.
    """
    if fd.net_income is None or fd.total_assets is None:
        return None

    score = 0
    avg_assets = fd.total_assets
    if fd.total_assets_prev is not None:
        avg_assets = (fd.total_assets + fd.total_assets_prev) / 2

    # --- Profitability (4 signals) ---

    # F1: Positive net income
    if fd.net_income > 0:
        score += 1

    # F2: Positive ROA (net_income / avg_assets)
    if avg_assets > 0 and fd.net_income / avg_assets > 0:
        score += 1

    # F3: Positive operating cash flow
    if fd.operating_cf is not None and fd.operating_cf > 0:
        score += 1

    # F4: Cash flow > net income (accrual quality)
    if fd.operating_cf is not None and fd.operating_cf > fd.net_income:
        score += 1

    # --- Leverage / Liquidity (3 signals) ---

    # F5: Decrease in leverage (long-term debt / avg assets)
    if fd.long_term_debt is not None and fd.long_term_debt_prev is not None:
        if avg_assets > 0 and fd.total_assets_prev is not None and fd.total_assets_prev > 0:
            curr_leverage = fd.long_term_debt / avg_assets
            prev_leverage = fd.long_term_debt_prev / fd.total_assets_prev
            if curr_leverage < prev_leverage:
                score += 1

    # F6: Increase in current ratio
    if (
        fd.current_assets is not None
        and fd.current_liabilities is not None
        and fd.current_assets_prev is not None
        and fd.current_liabilities_prev is not None
        and fd.current_liabilities > 0
        and fd.current_liabilities_prev > 0
    ):
        curr_ratio = fd.current_assets / fd.current_liabilities
        prev_ratio = fd.current_assets_prev / fd.current_liabilities_prev
        if curr_ratio > prev_ratio:
            score += 1

    # F7: No new shares issued (shares outstanding didn't increase)
    # Only award if we can verify no dilution occurred.
    if fd.shares_outstanding is not None:
        shares_prev = getattr(fd, "shares_outstanding_prev", None)
        if shares_prev is not None:
            if fd.shares_outstanding <= shares_prev:
                score += 1
        else:
            pass  # No prev data → conservative: skip (don't award)

    # --- Operating Efficiency (2 signals) ---

    # F8: Increase in gross margin
    if (
        fd.gross_profit is not None
        and fd.revenue is not None
        and fd.gross_profit_prev is not None
        and fd.revenue_prev is not None
        and fd.revenue > 0
        and fd.revenue_prev > 0
    ):
        curr_margin = fd.gross_profit / fd.revenue
        prev_margin = fd.gross_profit_prev / fd.revenue_prev
        if curr_margin > prev_margin:
            score += 1

    # F9: Increase in asset turnover
    if (
        fd.revenue is not None
        and fd.revenue_prev is not None
        and fd.total_assets_prev is not None
        and avg_assets > 0
        and fd.total_assets_prev > 0
    ):
        curr_turnover = fd.revenue / avg_assets
        prev_turnover = fd.revenue_prev / fd.total_assets_prev
        if curr_turnover > prev_turnover:
            score += 1

    return float(score)


def accruals_ratio(fd: FinancialData) -> float | None:
    """Accruals ratio = (Net Income - Operating CF) / Total Assets.

    Lower accruals (more negative) indicate higher earnings quality.
    Returns None if critical fields are missing.
    """
    if fd.net_income is None or fd.operating_cf is None or fd.total_assets is None:
        return None
    if fd.total_assets == 0:
        return None
    return (fd.net_income - fd.operating_cf) / fd.total_assets
