"""Backtest module for pair trading strategy"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


def calculate_zscore(spread: np.ndarray, window: int = 21) -> pd.Series:
    """Calculate rolling Z-score for the spread"""
    spread_series = pd.Series(spread)
    mean = spread_series.rolling(center=False, window=window).mean()
    std = spread_series.rolling(center=False, window=window).std()
    x = spread_series.rolling(center=False, window=1).mean()
    zscore = (x - mean) / std
    return zscore


def calculate_half_life(spread: np.ndarray) -> float:
    """Calculate mean reversion half-life using Ornstein-Uhlenbeck formula"""
    import statsmodels.api as sm

    df_spread = pd.DataFrame(spread, columns=["spread"])
    spread_lag = df_spread.spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params.iloc[1], 0) if res.params.iloc[1] < 0 else 0
    return halflife


class BacktestResult:
    """Container for backtest results"""

    def __init__(self):
        self.initial_capital: float = 0
        self.final_capital: float = 0
        self.total_return: float = 0
        self.annualized_return: float = 0
        self.sharpe_ratio: float = 0
        self.max_drawdown: float = 0
        self.win_rate: float = 0
        self.profit_loss_ratio: float = 0
        self.total_trades: int = 0
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

    def to_dict(self) -> Dict:
        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "profit_loss_ratio": self.profit_loss_ratio,
            "total_trades": self.total_trades,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }


class Trade:
    """Represents a single trade"""

    def __init__(
        self,
        pair: str,
        base_market: str,
        quote_market: str,
        direction: str,
        entry_date: str,
        entry_price_base: float,
        entry_price_quote: float,
        base_size: int,
        quote_size: int,
        entry_zscore: float,
        hedge_ratio: float,
        commission: float = 0,
    ):
        self.pair = pair
        self.base_market = base_market
        self.quote_market = quote_market
        self.direction = direction  # "long_spread" or "short_spread"
        self.entry_date = entry_date
        self.entry_price_base = entry_price_base
        self.entry_price_quote = entry_price_quote
        self.base_size = base_size
        self.quote_size = quote_size
        self.entry_zscore = entry_zscore
        self.hedge_ratio = hedge_ratio
        self.commission = commission  # Total commission paid for this trade (entry + exit)

        self.exit_date: Optional[str] = None
        self.exit_price_base: Optional[float] = None
        self.exit_price_quote: Optional[float] = None
        self.exit_zscore: Optional[float] = None
        self.pnl: Optional[float] = None
        self.is_closed: bool = False

    def close(
        self,
        exit_date: str,
        exit_price_base: float,
        exit_price_quote: float,
        exit_zscore: float,
    ):
        self.exit_date = exit_date
        self.exit_price_base = exit_price_base
        self.exit_price_quote = exit_price_quote
        self.exit_zscore = exit_zscore
        self.is_closed = True

        # Calculate PnL (gross, before commission)
        # 做多价差: 买入 base, 卖出 quote -> base 盈利 - quote 亏损
        # 做空价差: 卖出 base, 买入 quote -> base 亏损 - quote 盈利
        if self.direction == "long_spread":
            base_pnl = (exit_price_base - self.entry_price_base) * self.base_size
            quote_pnl = (self.entry_price_quote - exit_price_quote) * self.quote_size
        else:  # short_spread
            base_pnl = (self.entry_price_base - exit_price_base) * self.base_size
            quote_pnl = (exit_price_quote - self.entry_price_quote) * self.quote_size

        gross_pnl = base_pnl + quote_pnl
        self.pnl = gross_pnl - self.commission  # Net PnL after commission

    def to_dict(self) -> Dict:
        return {
            "pair": self.pair,
            "base_market": self.base_market,
            "quote_market": self.quote_market,
            "direction": self.direction,
            "entry_date": self.entry_date,
            "entry_price_base": self.entry_price_base,
            "entry_price_quote": self.entry_price_quote,
            "base_size": self.base_size,
            "quote_size": self.quote_size,
            "entry_zscore": self.entry_zscore,
            "hedge_ratio": self.hedge_ratio,
            "exit_date": self.exit_date,
            "exit_price_base": self.exit_price_base,
            "exit_price_quote": self.exit_price_quote,
            "exit_zscore": self.exit_zscore,
            "pnl": self.pnl,
        }


def run_backtest(
    df_prices: pd.DataFrame,
    df_pairs: pd.DataFrame,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000,
    zscore_threshold: float = 1.5,
    half_life_threshold: int = 8,
    window: int = 21,
    usd_per_trade: float = 50000,
    commission_per_trade: float = 0,
    close_at_zscore_cross: bool = True,
) -> BacktestResult:
    """
    Run backtest for pair trading strategy.

    Args:
        df_prices: Historical price data with datetime index
        df_pairs: Cointegrated pairs with columns [base_market, quote_market, hedge_ratio, half_life]
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_capital: Initial capital in USD
        zscore_threshold: Z-score threshold for entry
        half_life_threshold: Half-life threshold for entry
        window: Z-score calculation window
        usd_per_trade: USD amount per trade
        commission_per_trade: Commission/fee per trade (in USD, applied at entry and exit)
        close_at_zscore_cross: Close position when z-score crosses zero

    Returns:
        BacktestResult object
    """
    # Filter data by date range
    df_prices = df_prices.copy()
    df_prices["datetime"] = pd.to_datetime(df_prices["datetime"])
    df_prices = df_prices[
        (df_prices["datetime"] >= start_date) & (df_prices["datetime"] <= end_date)
    ]
    df_prices = df_prices.set_index("datetime")

    if len(df_prices) < window + 1:
        raise ValueError("Insufficient data for backtest")

    # Initialize result
    result = BacktestResult()
    result.initial_capital = initial_capital
    capital = initial_capital

    # Track open positions
    open_trades: List[Trade] = []
    all_trades: List[Trade] = []

    # Pre-calculate z-scores for all pairs
    pair_zscores: Dict[str, Tuple[np.ndarray, pd.Series]] = {}

    for _, row in df_pairs.iterrows():
        base_market = row["base_market"]
        quote_market = row["quote_market"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]

        # Skip if half-life exceeds threshold
        if half_life > half_life_threshold:
            continue

        # Skip if markets not in data
        if base_market not in df_prices.columns or quote_market not in df_prices.columns:
            continue

        # Calculate spread and z-score
        series_1 = df_prices[base_market].values.astype(float)
        series_2 = df_prices[quote_market].values.astype(float)

        spread = series_1 - (hedge_ratio * series_2)
        zscore = calculate_zscore(spread, window)

        pair_key = f"{base_market}/{quote_market}"
        pair_zscores[pair_key] = (spread, zscore)

    # Get list of dates for iteration
    dates = df_prices.index.tolist()

    # Track equity curve
    equity_curve = []

    # Iterate through each day
    for i, date in enumerate(dates):
        current_date = pd.Timestamp(date)

        # Skip first 'window' days (not enough data for z-score)
        if i < window:
            continue

        # Check open positions for exit
        trades_to_close = []

        for trade in open_trades:
            pair_key = f"{trade.base_market}/{trade.quote_market}"

            if pair_key not in pair_zscores:
                continue

            spread, zscore_series = pair_zscores[pair_key]
            zscore_current = zscore_series.iloc[i]

            if np.isnan(zscore_current):
                continue

            z_score_traded = trade.entry_zscore
            z_score_level_check = abs(zscore_current) > zscore_threshold

            if close_at_zscore_cross:
                z_score_cross_check = (zscore_current < 0 and z_score_traded > 0) or (
                    zscore_current > 0 and z_score_traded < 0
                )
            else:
                z_score_cross_check = abs(zscore_current) < 0.2

            if z_score_level_check and z_score_cross_check:
                # Close position
                base_price = df_prices[trade.base_market].iloc[i]
                quote_price = df_prices[trade.quote_market].iloc[i]

                trade.close(
                    exit_date=str(current_date.date()),
                    exit_price_base=base_price,
                    exit_price_quote=quote_price,
                    exit_zscore=zscore_current,
                )

                capital += trade.pnl
                trades_to_close.append(trade)
                all_trades.append(trade)

        # Remove closed trades
        for trade in trades_to_close:
            open_trades.remove(trade)

        # Check for new entries
        for _, row in df_pairs.iterrows():
            base_market = row["base_market"]
            quote_market = row["quote_market"]
            hedge_ratio = row["hedge_ratio"]
            half_life = row["half_life"]

            # Skip if half-life exceeds threshold
            if half_life > half_life_threshold:
                continue

            # Skip if markets not in data
            if base_market not in df_prices.columns or quote_market not in df_prices.columns:
                continue

            # Check if already have position on this pair
            has_position = any(
                t.base_market == base_market and t.quote_market == quote_market
                for t in open_trades
            )
            if has_position:
                continue

            pair_key = f"{base_market}/{quote_market}"
            if pair_key not in pair_zscores:
                continue

            spread, zscore_series = pair_zscores[pair_key]
            zscore_current = zscore_series.iloc[i]

            if np.isnan(zscore_current):
                continue

            # Check entry conditions
            if abs(zscore_current) >= zscore_threshold:
                base_price = df_prices[base_market].iloc[i]
                quote_price = df_prices[quote_market].iloc[i]

                # Calculate position size
                base_quantity = usd_per_trade / base_price
                quote_quantity = usd_per_trade / quote_price
                base_size = int(base_quantity)
                quote_size = int(quote_quantity)

                if base_size < 1 or quote_size < 1:
                    continue

                # Determine direction
                if zscore_current < 0:
                    direction = "long_spread"  # Buy base, sell quote
                else:
                    direction = "short_spread"  # Sell base, buy quote

                # Calculate commission (entry + exit)
                total_commission = 2 * commission_per_trade

                trade = Trade(
                    pair=pair_key,
                    base_market=base_market,
                    quote_market=quote_market,
                    direction=direction,
                    entry_date=str(current_date.date()),
                    entry_price_base=base_price,
                    entry_price_quote=quote_price,
                    base_size=base_size,
                    quote_size=quote_size,
                    entry_zscore=zscore_current,
                    hedge_ratio=hedge_ratio,
                    commission=total_commission,
                )

                open_trades.append(trade)

        # Record equity
        equity_curve.append(
            {
                "date": str(current_date.date()),
                "capital": capital,
                "open_positions": len(open_trades),
            }
        )

    # Close any remaining positions at the end
    for trade in open_trades:
        last_date = dates[-1]
        base_price = df_prices[trade.base_market].iloc[-1]
        quote_price = df_prices[trade.quote_market].iloc[-1]

        trade.close(
            exit_date=str(pd.Timestamp(last_date).date()),
            exit_price_base=base_price,
            exit_price_quote=quote_price,
            exit_zscore=0,
        )

        capital += trade.pnl
        all_trades.append(trade)

    # Calculate final metrics
    result.final_capital = capital
    result.total_trades = len(all_trades)
    result.trades = [t.to_dict() for t in all_trades]
    result.equity_curve = equity_curve

    # Calculate performance metrics
    if initial_capital > 0:
        result.total_return = (capital - initial_capital) / initial_capital

        # Calculate days in backtest
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days = (end_dt - start_dt).days
        years = days / 365.0

        if years > 0:
            result.annualized_return = (1 + result.total_return) ** (1 / years) - 1

    # Calculate Sharpe ratio
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            prev_capital = equity_curve[i - 1]["capital"]
            curr_capital = equity_curve[i]["capital"]
            if prev_capital > 0:
                ret = (curr_capital - prev_capital) / prev_capital
                returns.append(ret)

        if len(returns) > 0 and np.std(returns) > 0:
            result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)

    # Calculate max drawdown
    if len(equity_curve) > 0:
        peak = equity_curve[0]["capital"]
        max_dd = 0

        for point in equity_curve:
            capital_val = point["capital"]
            if capital_val > peak:
                peak = capital_val
            dd = (peak - capital_val) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        result.max_drawdown = max_dd

    # Calculate win rate and profit/loss ratio
    if len(all_trades) > 0:
        winning_trades = [t for t in all_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in all_trades if t.pnl and t.pnl <= 0]

        result.win_rate = len(winning_trades) / len(all_trades)

        if len(winning_trades) > 0 and len(losing_trades) > 0:
            avg_win = np.mean([t.pnl for t in winning_trades])
            avg_loss = np.mean([abs(t.pnl) for t in losing_trades])
            result.profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    return result


def load_backtest_data(
    prices_path: str = None,
    pairs_path: str = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load data for backtesting.

    Returns:
        Tuple of (df_prices, df_pairs)
    """
    import os

    # Get default paths based on file location
    if prices_path is None or pairs_path is None:
        # Assume running from program directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        if prices_path is None:
            prices_path = os.path.join(base_dir, "program/market_price.csv")
        if pairs_path is None:
            pairs_path = os.path.join(base_dir, "program/cointegrated_pairs.csv")

    df_prices = pd.read_csv(prices_path, parse_dates=["datetime"])
    df_pairs = pd.read_csv(pairs_path)
    return df_prices, df_pairs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run pair trading backtest")
    parser.add_argument("--start", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2024-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    parser.add_argument("--zscore", type=float, default=1.5, help="Z-score threshold")
    parser.add_argument("--halflife", type=int, default=8, help="Half-life threshold")
    parser.add_argument("--window", type=int, default=21, help="Z-score window")
    parser.add_argument("--usd", type=float, default=50000, help="USD per trade")

    args = parser.parse_args()

    # Load data
    print("Loading data...")
    df_prices, df_pairs = load_backtest_data()

    print(f"Running backtest from {args.start} to {args.end}...")
    result = run_backtest(
        df_prices=df_prices,
        df_pairs=df_pairs,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        zscore_threshold=args.zscore,
        half_life_threshold=args.halflife,
        window=args.window,
        usd_per_trade=args.usd,
    )

    # Print results
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Capital:   ${result.final_capital:,.2f}")
    print(f"Total Return:    {result.total_return * 100:.2f}%")
    print(f"Annual Return:   {result.annualized_return * 100:.2f}%")
    print(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown:    {result.max_drawdown * 100:.2f}%")
    print(f"Win Rate:        {result.win_rate * 100:.2f}%")
    print(f"Profit/Loss:     {result.profit_loss_ratio:.2f}")
    print(f"Total Trades:    {result.total_trades}")
    print("=" * 50)

    # Save results
    output_path = "backtest_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_path}")
