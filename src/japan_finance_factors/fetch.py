"""Optional data fetching wrappers for edinet-mcp and stockprice-mcp.

These functions require optional dependencies:
  pip install japan-finance-factors[edinet]       # for fetch_financial_data
  pip install japan-finance-factors[stockprice]   # for fetch_price_data
  pip install japan-finance-factors[all]          # for both
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

from japan_finance_factors._models import FinancialData, MonetaryUnit, PriceData


def _is_edinet_available() -> bool:
    try:
        import edinet_mcp  # noqa: F401

        return True
    except ImportError:
        return False


def _is_stockprice_available() -> bool:
    try:
        import yfinance_mcp  # noqa: F401

        return True
    except ImportError:
        return False


async def fetch_financial_data(
    edinet_code: str,
    *,
    period: str | None = None,
    doc_type: str = "annual_report",
) -> FinancialData:
    """Fetch financial data from EDINET and convert to FinancialData.

    Requires: ``pip install japan-finance-factors[edinet]``

    Args:
        edinet_code: EDINET company code (e.g., "E02144").
        period: Fiscal year (e.g., "2024"). None for most recent.
        doc_type: Document type ("annual_report", "quarterly_report").

    Returns:
        FinancialData with values in thousands of JPY (千円).
        Call ``.normalized()`` to convert to JPY.
    """
    if not _is_edinet_available():
        raise ImportError(
            "edinet-mcp is required: pip install japan-finance-factors[edinet]"
        )

    from edinet_mcp import EdinetClient, calculate_metrics

    async with EdinetClient() as client:
        stmt = await client.get_financial_statements(
            edinet_code, doc_type=doc_type, period=period
        )

    metrics = calculate_metrics(stmt)
    raw: dict[str, Any] = metrics.get("raw_values", {})

    # Extract values from raw_values (千円 units)
    def _get(key: str) -> float | None:
        val = raw.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Map edinet-mcp raw_values keys to FinancialData fields
    fd = FinancialData(
        edinet_code=edinet_code,
        period_end=_parse_period_end(stmt),
        published_at=_parse_published_at(stmt),
        unit=MonetaryUnit.THOUSAND_JPY,
        # Income statement
        revenue=_get("売上高"),
        cost_of_sales=_get("売上原価"),
        gross_profit=_get("売上総利益"),
        operating_income=_get("営業利益"),
        ordinary_income=_get("経常利益"),
        net_income=_get("当期純利益"),
        depreciation=_get("減価償却費"),
        interest_expense=_get("支払利息"),
        # Balance sheet
        total_assets=_get("総資産"),
        current_assets=_get("流動資産"),
        cash_and_deposits=_get("現金及び預金"),
        receivables=_get("売掛金"),
        inventories=_get("棚卸資産"),
        total_liabilities=_get("負債合計"),
        current_liabilities=_get("流動負債"),
        short_term_debt=_get("短期借入金"),
        long_term_debt=_get("長期借入金"),
        total_equity=_get("純資産"),
        retained_earnings=_get("利益剰余金"),
        # Cash flow
        operating_cf=_get("営業CF"),
        investing_cf=_get("投資CF"),
        capex=_get("設備投資"),
    )

    return fd


async def fetch_price_data(
    ticker: str,
    *,
    lookback_days: int = 365,
    as_of: datetime | None = None,
) -> PriceData:
    """Fetch price history from yfinance and convert to PriceData.

    Requires: ``pip install japan-finance-factors[stockprice]``

    Args:
        ticker: 4-digit TSE stock code (e.g., "7203").
        lookback_days: Number of calendar days of history to fetch.
        as_of: End date for price data. Defaults to today.

    Returns:
        PriceData with daily OHLCV prices.
    """
    if not _is_stockprice_available():
        raise ImportError(
            "stockprice-mcp is required: pip install japan-finance-factors[stockprice]"
        )

    from yfinance_mcp import YfinanceClient

    end = as_of or datetime.now()
    start = end - timedelta(days=lookback_days)

    client = YfinanceClient()
    try:
        # Get price history
        hist = await client.get_stock_history(
            ticker,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        )

        # Get latest snapshot for market cap
        latest = await client.get_stock_price(ticker)
    finally:
        if hasattr(client, "close"):
            await client.close()

    prices: list[dict[str, Any]] = []
    if hist is not None:
        for row in hist.rows:
            prices.append({
                "date": row.get("date", ""),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
            })

    market_cap = None
    if latest is not None and latest.market_cap is not None:
        market_cap = float(latest.market_cap)

    return PriceData(
        ticker=ticker,
        prices=prices,
        market_cap=market_cap,
    )


def _parse_period_end(stmt: Any) -> date | None:
    """Extract period_end from FinancialStatement."""
    try:
        filing = stmt.filing
        if hasattr(filing, "period_end") and filing.period_end is not None:
            if isinstance(filing.period_end, date):
                return filing.period_end
            return date.fromisoformat(str(filing.period_end))
    except (AttributeError, ValueError):
        pass
    return None


def _parse_published_at(stmt: Any) -> datetime | None:
    """Extract filing_date as datetime from FinancialStatement."""
    try:
        filing = stmt.filing
        if hasattr(filing, "filing_date") and filing.filing_date is not None:
            d = filing.filing_date
            if isinstance(d, datetime):
                return d
            if isinstance(d, date):
                return datetime(d.year, d.month, d.day)
            return datetime.fromisoformat(str(d))
    except (AttributeError, ValueError):
        pass
    return None


def fetch_financial_data_sync(
    edinet_code: str,
    *,
    period: str | None = None,
    doc_type: str = "annual_report",
) -> FinancialData:
    """Synchronous wrapper for ``fetch_financial_data``."""
    return asyncio.run(
        fetch_financial_data(edinet_code, period=period, doc_type=doc_type)
    )


def fetch_price_data_sync(
    ticker: str,
    *,
    lookback_days: int = 365,
    as_of: datetime | None = None,
) -> PriceData:
    """Synchronous wrapper for ``fetch_price_data``."""
    return asyncio.run(
        fetch_price_data(ticker, lookback_days=lookback_days, as_of=as_of)
    )
