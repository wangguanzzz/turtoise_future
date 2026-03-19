"""Command-line entry point for backtest"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from turtoise_future.strategies.pair_trading.backtest import run_backtest, load_backtest_data
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Run pair trading backtest")
    parser.add_argument("--start", type=str, default="2025-11-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-03-17", help="End date (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    parser.add_argument("--zscore", type=float, default=1.5, help="Z-score threshold")
    parser.add_argument("--halflife", type=int, default=8, help="Half-life threshold")
    parser.add_argument("--window", type=int, default=21, help="Z-score window")
    parser.add_argument("--usd", type=float, default=50000, help="USD per trade")
    parser.add_argument("--commission", type=float, default=0, help="Commission per trade (USD, applied at entry and exit)")
    parser.add_argument("--output", type=str, default="backtest_result.json", help="Output file")

    args = parser.parse_args()

    # Change to program directory
    program_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(program_dir)

    # Load data
    print("Loading data...")
    try:
        df_prices, df_pairs = load_backtest_data()
        print(f"Loaded {len(df_prices)} price records and {len(df_pairs)} pairs")
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Make sure market_price.csv and cointegrated_pairs.csv exist in program directory")
        sys.exit(1)

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
        commission_per_trade=args.commission,
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
    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
