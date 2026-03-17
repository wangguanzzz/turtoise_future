# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Turtoise Future is a quantitative trading bot for Chinese commodity futures, implementing two primary strategies:
1. **Cointegration-based pair trading**: Identifies cointegrated futures contracts and executes mean-reversion trades.
2. **Supervised learning classification**: Builds binary classification models to predict price movements for individual contracts.

The system uses akshare for Chinese market data and includes backtesting capabilities.

## Development Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure you have an internet connection for akshare data fetching.
3. No API keys are required for data access (public akshare data).

## Common Commands

### Running the Cointegration Pair Trading Bot
```bash
cd program
python main.py
```
Configure `FIND_COINTEGRATED`, `PLACE_TRADES`, and `MANAGE_EXITS` flags in `constants.py` to control which stages execute.

### Running Supervised Trading Model Training
```bash
cd program
python supervised_trading.py
```
Configure `PREPARE_DATA` and `GENERATE_MODEL` flags in `constants.py`.

### Running Individual Tests
```bash
cd program
python test.py
```
The `test.py` file currently tests HMM feature addition. Additional tests can be added here.

### Data Preparation
The system automatically downloads market data via akshare. Initial data fetching occurs when `construct_market_prices()` is called (during cointegration analysis). Market reference data is cached in `market_reference.csv` and price data in `market_price.csv`.

## Architecture

### Two Independent Execution Paths
- **Main trading loop** (`main.py`): Cointegration pipeline for pair trading
- **Supervised training** (`supervised_trading.py`): Machine learning pipeline for directional predictions

### Modular Function Organization
Functions are separated by concern in `func_*.py` files:
- `func_public.py`: Data fetching from akshare and market utilities
- `func_private.py`: (Currently minimal) Private API interactions
- `func_cointegration.py`: Cointegration tests, half-life, z-score calculations
- `func_entry_pairs.py`: Entry logic for pair trades
- `func_exit_pairs.py`: Exit logic for pair trades
- `func_prepare_data.py`: Data preparation for supervised learning
- `func_select_feature.py`: Feature selection for classification models
- `func_binary_classification.py`: Model training and evaluation
- `func_hmm.py`: Hidden Markov Model feature generation
- `func_messaging.py`: Notification utilities
- `func_utils.py`: General helper functions
- `func_bot_agent.py`: (Likely) Bot agent logic

### Configuration
`constants.py` contains all tunable parameters:
- Mode selection (`DEVELOPMENT`/`PRODUCTION`)
- Pipeline control flags (`FIND_COINTEGRATED`, `PLACE_TRADES`, etc.)
- Trading parameters (`ZSCORE_THRESH`, `USD_PER_TRADE`, etc.)
- Commodity dictionary mapping contract codes to Chinese names and contract sizes
- Supervised learning thresholds

### Data Flow
1. **Cointegration pipeline**: Fetch all contracts → Calculate cointegrated pairs → Store in `cointegrated_pairs.csv` → Generate entry/exit signals
2. **Supervised pipeline**: Prepare contract data → Select features → Train binary classifiers → Output results to `result/{direction}_result.csv`

### Key Data Files
- `market_reference.csv`: Auto-generated cached contract metadata from akshare
- `market_price.csv`: Auto-generated historical price data for all contracts
- `cointegrated_pairs.csv`: Auto-generated discovered cointegrated pairs with hedge ratios
- `data/`: Auto-generated directory containing individual contract CSV files (created by supervised pipeline)
- `result/`: Auto-generated directory containing model evaluation results (created by supervised pipeline)

- `visualize.ipynb`: Jupyter notebook for visualizing cointegration results and spreads

### Strategy Management
`stratmanager.py` provides a `StrategyManager` class for backtesting moving average crossover strategies on individual contracts.

## Notes
- The codebase uses Chinese commodity futures symbols (e.g., 'V0' for PVC, 'P0' for palm oil)
- All data is fetched from public Sina Finance via akshare
- The supervised learning pipeline generates models per contract per direction (long/short)
- Cointegration pairs are evaluated daily (configurable via `RESOLUTION`)