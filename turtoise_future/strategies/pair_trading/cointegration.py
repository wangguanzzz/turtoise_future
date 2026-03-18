"""Cointegration analysis for pair trading"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
from typing import List, Dict, Any, Tuple
from ...config.settings import settings


def calculate_half_life(spread: np.ndarray) -> float:
    """Calculate mean reversion half-life using Ornstein-Uhlenbeck formula"""
    df_spread = pd.DataFrame(spread, columns=["spread"])
    spread_lag = df_spread.spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params[1], 0)
    return halflife


def calculate_zscore(spread: np.ndarray, window: int = None) -> pd.Series:
    """Calculate rolling Z-score for the spread"""
    if window is None:
        window = settings.window

    spread_series = pd.Series(spread)
    mean = spread_series.rolling(center=False, window=window).mean()
    std = spread_series.rolling(center=False, window=window).std()
    x = spread_series.rolling(center=False, window=1).mean()
    zscore = (x - mean) / std
    return zscore


def calculate_cointegration(
    series_1: np.ndarray, series_2: np.ndarray
) -> Tuple[int, float, float]:
    """
    Calculate cointegration between two series.

    Returns:
        Tuple of (coint_flag, hedge_ratio, half_life)
    """
    series_1 = np.array(series_1).astype(float)
    series_2 = np.array(series_2).astype(float)

    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]

    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]

    spread = series_1 - (hedge_ratio * series_2)
    half_life = calculate_half_life(spread)

    t_check = coint_t < critical_value
    coint_flag = 1 if p_value < 0.002 and t_check else 0

    return coint_flag, hedge_ratio, half_life


def find_cointegrated_pairs(
    df_market_prices: pd.DataFrame, max_half_life: int = None
) -> List[Dict[str, Any]]:
    """
    Find all cointegrated pairs in the market data.

    Args:
        df_market_prices: DataFrame with datetime index and contract columns
        max_half_life: Maximum half-life threshold

    Returns:
        List of dictionaries containing pair information
    """
    if max_half_life is None:
        max_half_life = settings.max_half_life

    markets = df_market_prices.columns.to_list()
    criteria_met_pairs = []

    for i, base_market in enumerate(markets[:-1]):
        series_1 = df_market_prices[base_market].values.astype(float).tolist()

        for quote_market in markets[i + 1 :]:
            series_2 = df_market_prices[quote_market].values.astype(float).tolist()

            coint_flag, hedge_ratio, half_life = calculate_cointegration(series_1, series_2)

            if coint_flag == 1 and half_life <= max_half_life and half_life > 0:
                criteria_met_pairs.append(
                    {
                        "base_market": base_market,
                        "quote_market": quote_market,
                        "hedge_ratio": hedge_ratio,
                        "half_life": half_life,
                    }
                )

    return criteria_met_pairs


def store_cointegration_results(df_market_prices: pd.DataFrame) -> str:
    """Store cointegration analysis results to CSV"""
    criteria_met_pairs = find_cointegrated_pairs(df_market_prices)

    from pathlib import Path
    data_dir = Path(__file__).parent.parent.parent / "program"
    data_dir.mkdir(parents=True, exist_ok=True)

    df_criteria_met = pd.DataFrame(criteria_met_pairs)
    df_criteria_met.to_csv(data_dir / "cointegrated_pairs.csv")

    print(f"Found {len(criteria_met_pairs)} cointegrated pairs")
    print("Cointegration results saved to cointegrated_pairs.csv")
    return "saved"
