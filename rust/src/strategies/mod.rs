//! Strategies module

pub mod cointegration;
pub mod entry;
pub mod exit;

pub use cointegration::{calculate_half_life, calculate_zscore, calculate_cointegration, find_cointegrated_pairs};
pub use entry::{find_entry_signals, is_open_position};
pub use exit::manage_trade_exits;
