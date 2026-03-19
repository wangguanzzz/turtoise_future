# Turtoise Future

A quantitative trading bot for Chinese commodity futures, implementing two primary strategies:

1. **Cointegration-based pair trading** - Identifies cointegrated futures contracts and executes mean-reversion trades
2. **Supervised learning classification** - Builds binary classification models to predict price movements

## Features

- Fetches real-time market data from Chinese futures exchanges via akshare
- Cointegration analysis to find trading pairs with mean-reversion properties
- Z-score based entry/exit signals for pair trading
- Binary classification models (long/short) using supervised learning
- Hidden Markov Model (HMM) feature engineering
- Web visualization dashboard for analysis results

## Installation

```bash
pip install -r requirements.txt
```

## Project Structure

```
turtoise_future/
├── program/                    # Entry points
│   ├── main.py               # Pair trading execution
│   └── supervised_trading.py # ML model training
├── turtoise_future/          # Core package
│   ├── config/               # Settings and commodity definitions
│   ├── data/                 # Data fetching and caching
│   ├── strategies/           # Trading strategies
│   │   ├── pair_trading/    # Cointegration pair trading
│   │   └── supervised/      # ML classification models
│   ├── execution/           # Order and position management
│   └── utils/                # Utilities (logging, validation)
└── web/                      # Streamlit visualization app
```

## Usage

### 1. Cointegration Pair Trading

```bash
cd program
python main.py
```

Configure pipeline stages in `turtoise_future/config/settings.py`:

| Flag | Description |
|------|-------------|
| `find_cointegrated` | Discover cointegrated pairs |
| `place_trades` | Generate entry signals |
| `manage_exits` | Manage trade exits |

### 2. Supervised Learning Trading

```bash
cd program
python supervised_trading.py
```

Configure in settings:
| Flag | Description |
|------|-------------|
| `prepare_data` | Prepare training data |
| `generate_model` | Train classification models |

### 3. Web Visualization

```bash
cd web
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Key parameters in `turtoise_future/config/settings.py`:

- **Resolution**: Data timeframe (1MIN, 5MIN, 15MIN, 30MIN, 1HOUR, 1DAY)
- **zscore_threshold**: Entry threshold (default: 1.5)
- **max_half_life**: Maximum half-life for pairs (default: 24)
- **usd_per_trade**: Position size per trade (default: 50000)

Commodity contracts are defined in `turtoise_future/config/commodities.py`.

## Data Files

- `market_reference.csv` - Cached contract metadata
- `market_price.csv` - Historical price data
- `cointegrated_pairs.csv` - Discovered cointegrated pairs
- `data/` - Individual contract data (generated)
- `result/` - Model evaluation results (generated)

## Requirements

- Python 3.8+
- akshare (Chinese market data)
- pandas, numpy, scipy, statsmodels
- scikit-learn (for ML models)
- streamlit (for web visualization)

## License

MIT
