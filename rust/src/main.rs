//! Turtoise Future - Chinese Commodity Futures Pair Trading Bot
//!
//! Rust implementation matching the Python version functionality.

mod config;
mod commodity;
#[cfg(feature = "web")]
mod web;

mod data;
mod strategies;
mod backtest;
mod execution;

use clap::Parser;
use log::info;
use std::path::PathBuf;

use crate::config::Args;
use crate::data::{load_market_prices, load_cointegrated_pairs, save_cointegrated_pairs};
use crate::strategies::{find_cointegrated_pairs, find_entry_signals, manage_trade_exits};
use crate::backtest::BacktestResult;

#[tokio::main]
async fn main() -> Result<(), String> {
    // Parse CLI arguments
    let args = Args::parse();

    // Initialize logger
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    // Check if running web server
    #[cfg(feature = "web")]
    if args.web {
        web::start_server(
            args.data_dir.to_string_lossy().to_string(),
            args.port,
        ).await;
        return Ok(());
    }

    info!("Starting Turtoise Future - Pair Trading (Rust)");

    // Resolve paths
    let prices_path = args.data_dir.join("market_price.csv");
    let pairs_path = args.data_dir.join("cointegrated_pairs.csv");
    let output_path = args.output_dir.join("backtest_result.json");

    // Find cointegrated pairs
    if args.find_cointegrated {
        info!("Fetching market prices...");

        let market_prices = load_market_prices(&prices_path)
            .map_err(|e| format!("Failed to load market prices: {}", e))?;

        info!("Storing cointegration results...");
        let pairs = find_cointegrated_pairs(&market_prices, args.max_half_life);

        save_cointegrated_pairs(&pairs_path, &pairs)?;
        println!("Found {} cointegrated pairs", pairs.len());
        println!("Cointegration results saved to cointegrated_pairs.csv");
    }

    // Backtest mode (if dates specified)
    if args.backtest_start.is_some() && args.backtest_end.is_some() {
        let start = args.backtest_start.as_ref().unwrap();
        let end = args.backtest_end.as_ref().unwrap();

        info!("Running backtest from {} to {}...", start, end);

        let prices = load_market_prices(&prices_path)
            .map_err(|e| format!("Failed to load market prices: {}", e))?;
        let pairs = load_cointegrated_pairs(&pairs_path)?;

        let result = run_backtest(
            &prices,
            &pairs,
            start,
            end,
            args.initial_capital,
            args.zscore_threshold,
            args.half_life_threshold,
            args.window,
            args.usd_per_trade,
            args.commission,
            args.close_at_zscore_cross,
        );

        // Print results
        println!("\n{}", "=".repeat(50));
        println!("BACKTEST RESULTS");
        println!("{}", "=".repeat(50));
        println!("Initial Capital: ${:.2}", result.initial_capital);
        println!("Final Capital:   ${:.2}", result.final_capital);
        println!("Total Return:    {:.2}%", result.total_return * 100.0);
        println!("Annual Return:   {:.2}%", result.annualized_return * 100.0);
        println!("Sharpe Ratio:    {:.2}", result.sharpe_ratio);
        println!("Max Drawdown:    {:.2}%", result.max_drawdown * 100.0);
        println!("Win Rate:        {:.2}%", result.win_rate * 100.0);
        println!("Profit/Loss:     {:.2}", result.profit_loss_ratio);
        println!("Total Trades:    {}", result.total_trades);
        println!("{}", "=".repeat(50));

        // Save results
        result.save(&output_path)?;
        println!("\nResults saved to {:?}", output_path);

        return Ok(());
    }

    // Live trading mode
    // Place trades
    if args.place_trades {
        info!("Finding trading opportunities...");

        let prices = load_market_prices(&prices_path)
            .map_err(|e| format!("Failed to load market prices: {}", e))?;

        find_entry_signals(&args, &pairs_path, &prices)?;
    }

    // Manage exits
    if args.manage_exits {
        info!("Managing exits...");

        let prices = load_market_prices(&prices_path)
            .map_err(|e| format!("Failed to load market prices: {}", e))?;

        let bot_agents_path = args.data_dir.join("bot_agents.json");
        manage_trade_exits(&args, &bot_agents_path, &prices)?;
    }

    info!("Trading cycle completed");

    Ok(())
}

fn run_backtest(
    prices: &crate::data::MarketPrices,
    pairs: &[crate::data::CointegratedPair],
    start_date: &str,
    end_date: &str,
    initial_capital: f64,
    zscore_threshold: f64,
    half_life_threshold: usize,
    window: usize,
    usd_per_trade: f64,
    commission_per_trade: f64,
    close_at_zscore_cross: bool,
) -> BacktestResult {
    crate::backtest::run_backtest(
        prices,
        pairs,
        start_date,
        end_date,
        initial_capital,
        zscore_threshold,
        half_life_threshold,
        window,
        usd_per_trade,
        commission_per_trade,
        close_at_zscore_cross,
    )
}
