# japan-finance-factors

Quantitative factor calculation for Japanese equities with point-in-time (PIT) safety.

## Features

- **10 quantitative factors** across 4 categories (value, momentum, quality, risk)
- **PIT-safe**: All calculations respect point-in-time constraints to prevent lookahead bias
- **Lightweight**: Only depends on pydantic; data source integrations are optional
- **Optional integrations**: Convenience wrappers for edinet-mcp and stockprice-mcp

## Installation

```bash
pip install japan-finance-factors

# With optional data source integrations
pip install japan-finance-factors[all]
```

## Quick Start

```python
from datetime import datetime
from japan_finance_factors import compute_factors, FinancialData, PriceData

# Prepare financial data (JPY units)
fd = FinancialData(
    ticker="7203",
    revenue=45_000_000_000_000,
    net_income=2_800_000_000_000,
    operating_income=3_500_000_000_000,
    total_assets=90_000_000_000_000,
    total_equity=35_000_000_000_000,
    operating_cf=4_500_000_000_000,
    capex=-1_800_000_000_000,
    market_cap=50_000_000_000_000,
    published_at=datetime(2025, 6, 25),
)

# Compute all factors
result = compute_factors(
    financial_data=fd,
    as_of=datetime(2025, 7, 1),
)

print(result.to_dict())
# {'ev_ebitda': 12.77, 'fcf_yield': 0.054, 'earnings_yield': 0.056, ...}
```

## Factors

| Category | Factor | Description |
|----------|--------|-------------|
| Value | `ev_ebitda` | Enterprise Value / EBITDA |
| Value | `fcf_yield` | Free Cash Flow / Market Cap |
| Value | `earnings_yield` | Net Income / Market Cap |
| Value | `book_to_market` | Book Value / Market Cap |
| Momentum | `mom_3m` | 3-month price return |
| Momentum | `mom_12m` | 12-month price return (12-1 convention) |
| Quality | `piotroski_f_score` | Piotroski F-Score (0-9) |
| Quality | `accruals_ratio` | (Net Income - Operating CF) / Total Assets |
| Risk | `realized_vol_60d` | 60-day annualized volatility |
| Risk | `max_drawdown_252d` | Maximum drawdown over 252 trading days |

## License

Apache-2.0
