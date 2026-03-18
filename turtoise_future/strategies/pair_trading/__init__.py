"""Pair trading strategy module"""

from .cointegration import (
    calculate_cointegration,
    calculate_half_life,
    calculate_zscore,
    store_cointegration_results,
)
from .entry import find_entry_signals
from .exit import manage_trade_exits

__all__ = [
    "calculate_cointegration",
    "calculate_half_life",
    "calculate_zscore",
    "store_cointegration_results",
    "find_entry_signals",
    "manage_trade_exits",
]
