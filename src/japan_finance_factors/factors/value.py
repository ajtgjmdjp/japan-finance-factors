"""Value factor calculations.

All functions accept a normalized ``FinancialData`` (JPY units)
and return the factor value or None if inputs are insufficient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import FinancialData


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    """Safe division returning None if inputs are missing or denominator is zero."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def ev_ebitda(fd: FinancialData) -> float | None:
    """Enterprise Value / EBITDA.

    EV = market_cap + total_debt - cash
    EBITDA = operating_income + depreciation
    """
    if fd.market_cap is None or fd.operating_income is None:
        return None
    total_debt = (fd.short_term_debt or 0) + (fd.long_term_debt or 0)
    cash = fd.cash_and_deposits or 0
    ev = fd.market_cap + total_debt - cash
    ebitda = fd.operating_income + (fd.depreciation or 0)
    return _safe_div(ev, ebitda)


def fcf_yield(fd: FinancialData) -> float | None:
    """Free Cash Flow Yield = FCF / Market Cap.

    FCF = Operating CF - CapEx
    """
    if fd.operating_cf is None or fd.market_cap is None:
        return None
    capex = abs(fd.capex or 0)
    fcf = fd.operating_cf - capex
    return _safe_div(fcf, fd.market_cap)


def earnings_yield(fd: FinancialData) -> float | None:
    """Earnings Yield = Net Income / Market Cap (inverse of P/E)."""
    return _safe_div(fd.net_income, fd.market_cap)


def book_to_market(fd: FinancialData) -> float | None:
    """Book-to-Market ratio = Total Equity / Market Cap (inverse of P/B)."""
    return _safe_div(fd.total_equity, fd.market_cap)
