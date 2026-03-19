//! Backtest module for pair trading strategy

pub mod engine;

pub use engine::{BacktestResult, Trade, run_backtest, load_backtest_data};
