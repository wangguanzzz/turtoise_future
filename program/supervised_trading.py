#!/usr/bin/env python
"""
Supervised learning trading strategy entry point.

Usage:
    python supervised_trading.py
"""

import sys
import csv
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtoise_future.config.settings import settings
from turtoise_future.config.commodities import COMMODITY_DICT
from turtoise_future.strategies.supervised import prepare_data, select_feature, train_model
from turtoise_future.utils.logger import setup_logger


def main():
    """Main supervised learning pipeline"""
    logger = setup_logger()
    logger.info("Starting Turtoise Future - Supervised Learning")

    # Prepare data
    if settings.prepare_data:
        logger.info("Preparing data...")
        prepare_data()

    # Generate models
    if settings.generate_model:
        logger.info("Training models...")
        directions = ["long", "short"]

        for direction in directions:
            output = []
            for contract in COMMODITY_DICT.keys():
                logger.info(f"Training {contract} - {direction}")
                try:
                    params, features = select_feature(contract, direction)
                    result = train_model(contract, direction, params, features)
                    output.append(result)
                except Exception as e:
                    logger.error(f"Error for {contract} {direction}: {e}")
                    traceback.print_exc()
                    continue

            # Save results
            filename = f"result/{direction}_result.csv"
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w", newline="") as file:
                writer = csv.writer(file)
                for row in output:
                    writer.writerow(row)

            logger.info(f"Saved {direction} results to {filename}")

    logger.info("Supervised learning pipeline completed")


if __name__ == "__main__":
    main()
