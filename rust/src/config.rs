//! Configuration and CLI arguments matching Python settings

use clap::Parser;
use std::path::PathBuf;

#[derive(Parser, Debug, Clone)]
#[clap(name = "turtoise_future")]
#[clap(about = "Chinese commodity futures pair trading bot", long_about = None)]
pub struct Args {
    /// Run mode: DEVELOPMENT or PRODUCTION
    #[clap(long, default_value = "DEVELOPMENT")]
    pub mode: String,

    /// Data resolution: 1MIN, 5MIN, 15MIN, 30MIN, 1HOUR, 1DAY
    #[clap(long, default_value = "1DAY")]
    pub resolution: String,

    /// Find cointegrated pairs
    #[clap(long)]
    pub find_cointegrated: bool,

    /// Place trades
    #[clap(long)]
    pub place_trades: bool,

    /// Manage trade exits
    #[clap(long)]
    pub manage_exits: bool,

    /// Prepare supervised learning data
    #[clap(long)]
    pub prepare_data: bool,

    /// Generate ML models
    #[clap(long)]
    pub generate_model: bool,

    /// Z-score calculation window
    #[clap(long, default_value = "21")]
    pub window: usize,

    /// Maximum half-life for pairs
    #[clap(long, default_value = "24")]
    pub max_half_life: usize,

    /// Z-score entry threshold
    #[clap(long, default_value = "1.5")]
    pub zscore_threshold: f64,

    /// Half-life threshold for entry
    #[clap(long, default_value = "8")]
    pub half_life_threshold: usize,

    /// USD amount per trade
    #[clap(long, default_value = "50000.0")]
    pub usd_per_trade: f64,

    /// Minimum collateral required
    #[clap(long, default_value = "1880.0")]
    pub usd_min_collateral: f64,

    /// Close at Z-score cross
    #[clap(long, default_value = "true")]
    pub close_at_zscore_cross: bool,

    /// Data directory (contains market_price.csv, cointegrated_pairs.csv)
    #[clap(long, default_value = ".")]
    pub data_dir: PathBuf,

    /// Output directory for results
    #[clap(long, default_value = ".")]
    pub output_dir: PathBuf,

    /// Backtest start date (YYYY-MM-DD)
    #[clap(long)]
    pub backtest_start: Option<String>,

    /// Backtest end date (YYYY-MM-DD)
    #[clap(long)]
    pub backtest_end: Option<String>,

    /// Initial capital for backtest
    #[clap(long, default_value = "100000.0")]
    pub initial_capital: f64,

    /// Commission per trade for backtest
    #[clap(long, default_value = "0.0")]
    pub commission: f64,

    /// Start web UI server
    #[clap(long)]
    pub web: bool,

    /// Web server port
    #[clap(long, default_value = "8080")]
    pub port: u16,
}

impl Default for Args {
    fn default() -> Self {
        Self {
            mode: "DEVELOPMENT".to_string(),
            resolution: "1DAY".to_string(),
            find_cointegrated: true,
            place_trades: true,
            manage_exits: true,
            prepare_data: false,
            generate_model: false,
            window: 21,
            max_half_life: 24,
            zscore_threshold: 1.5,
            half_life_threshold: 8,
            usd_per_trade: 50000.0,
            usd_min_collateral: 1880.0,
            close_at_zscore_cross: true,
            data_dir: PathBuf::from("."),
            output_dir: PathBuf::from("."),
            backtest_start: None,
            backtest_end: None,
            initial_capital: 100000.0,
            commission: 0.0,
            web: false,
            port: 8080,
        }
    }
}

impl Args {
    pub fn is_development(&self) -> bool {
        self.mode == "DEVELOPMENT"
    }
}
