"""Formatting utilities"""

from datetime import datetime
from typing import Union


def format_number(curr_num: Union[int, float], match_num: Union[int, float]) -> str:
    """
    Format a number to match the decimal places of another number.

    Args:
        curr_num: Number to format
        match_num: Number to match decimal places from

    Returns:
        Formatted string
    """
    curr_num_string = f"{curr_num}"
    match_num_string = f"{match_num}"

    if "." in match_num_string:
        match_decimals = len(match_num_string.split(".")[1])
        curr_num_string = f"{curr_num:.{match_decimals}f}"
        return curr_num_string
    else:
        return f"{int(curr_num)}"


def format_time(timestamp: datetime) -> str:
    """Format datetime to ISO format without microseconds"""
    return timestamp.replace(microsecond=0).isoformat()


def format_price(price: float, decimals: int = 2) -> str:
    """Format price with specified decimals"""
    return f"{price:.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage"""
    return f"{value * 100:.{decimals}f}%"


def format_currency(amount: float, currency: str = "¥") -> str:
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"
