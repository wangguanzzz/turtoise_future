"""Validation utilities"""

from typing import Tuple, Optional
import numpy as np


def validate_price(price: float) -> bool:
    """Validate price is positive"""
    return price > 0 and not np.isnan(price) and not np.isinf(price)


def validate_size(size: float, min_size: float = 1.0) -> bool:
    """Validate size is positive and meets minimum"""
    return size >= min_size and not np.isnan(size) and not np.isinf(size)


def validate_hedge_ratio(ratio: float) -> bool:
    """Validate hedge ratio is reasonable"""
    return ratio > 0 and not np.isnan(ratio) and not np.isinf(ratio)


def validate_zscore(zscore: float) -> bool:
    """Validate z-score is finite"""
    return not np.isnan(zscore) and not np.isinf(zscore)


def validate_contract_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate contract symbol format.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symbol:
        return False, "Symbol cannot be empty"

    if len(symbol) < 2:
        return False, "Symbol too short"

    # Check if it looks like a futures contract (e.g., cu2604, rb2105)
    if not symbol[:2].isalpha():
        return False, "Symbol should start with letters"

    return True, None
