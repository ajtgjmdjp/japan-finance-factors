"""Size factor calculations."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from japan_finance_factors._models import FinancialData


def log_market_cap(fd: FinancialData) -> float | None:
    """Natural log of market capitalization (JPY).

    Standard size factor used in Fama-French and similar models.
    """
    if fd.market_cap is None or fd.market_cap <= 0:
        return None
    return math.log(fd.market_cap)
