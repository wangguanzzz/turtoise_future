#!/usr/bin/env python
"""
Main entry point for pair trading strategy.

Usage:
    python main.py
"""

import sys
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtoise_future.config.settings import settings
from turtoise_future.data.cache import MarketCache
from turtoise_future.strategies.pair_trading import (
    store_cointegration_results,
    find_entry_signals,
    manage_trade_exits,
)
from turtoise_future.utils.logger import setup_logger


def main():
    """Main trading loop"""
    logger = setup_logger()
    logger.info("Starting Turtoise Future - Pair Trading")

    try:
        # Find cointegrated pairs
        if settings.find_cointegrated:
            logger.info("Fetching market prices...")
            cache = MarketCache()
            df_market_prices = cache.construct_market_prices()

            logger.info("Storing cointegration results...")
            result = store_cointegration_results(df_market_prices)
            if result != "saved":
                logger.error("Error saving cointegration results")
                sys.exit(1)

        # Place trades
        if settings.place_trades:
            logger.info("Finding trading opportunities...")
            find_entry_signals()

        # Manage exits
        if settings.manage_exits:
            logger.info("Managing exits...")
            manage_trade_exits()

        logger.info("Trading cycle completed")

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
