//! Entry logic for pair trading

use crate::config::Args;
use crate::data::{load_cointegrated_pairs, MarketPrices};
use crate::strategies::cointegration::calculate_zscore;
use std::fs;
use std::path::Path;

/// Bot agent position data (matches Python structure)
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BotAgent {
    pub market_1: String,
    pub market_2: String,
    pub market_1_cn: String,
    pub market_2_cn: String,
    pub hedge_ratio: f64,
    pub z_score: f64,
    pub half_life: f64,
    pub order_id_m1: String,
    pub order_m1_size: String,
    pub order_m1_side: String,
    pub order_time_m1: String,
    pub order_id_m2: String,
    pub order_m2_size: String,
    pub order_m2_side: String,
    pub order_time_m2: String,
    pub pair_status: String,
    pub comments: String,
}

/// Load open positions from JSON file
pub fn load_open_positions(path: &Path) -> Vec<BotAgent> {
    match fs::read_to_string(path) {
        Ok(content) => serde_json::from_str(&content).unwrap_or_default(),
        Err(_) => Vec::new(),
    }
}

/// Save open positions to JSON file
pub fn save_open_positions(path: &Path, agents: &[BotAgent]) -> Result<(), String> {
    let content = serde_json::to_string_pretty(agents)
        .map_err(|e| format!("Failed to serialize: {}", e))?;
    fs::write(path, content).map_err(|e| format!("Failed to write file: {}", e))?;
    Ok(())
}

/// Check if a market already has an open position
pub fn is_open_position(bot_agents: &[BotAgent], market: &str) -> bool {
    bot_agents.iter().any(|agent| {
        agent.market_1 == market || agent.market_2 == market
    })
}

/// Find entry signals for cointegrated pairs
pub fn find_entry_signals(
    args: &Args,
    pairs_path: &Path,
    prices: &MarketPrices,
) -> Result<usize, String> {
    // Load cointegrated pairs
    let pairs = load_cointegrated_pairs(pairs_path)?;

    // Load existing positions
    let bot_agents_path = args.data_dir.join("bot_agents.json");
    let mut bot_agents = load_open_positions(&bot_agents_path);

    let mut new_positions = 0;

    for pair in &pairs {
        let series_1 = prices.get_series(&pair.base_market);
        let series_2 = prices.get_series(&pair.quote_market);

        if series_1.is_empty() || series_1.len() != series_2.len() {
            continue;
        }

        // Calculate spread and z-score
        let spread: Vec<f64> = series_1
            .iter()
            .zip(series_2.iter())
            .map(|(s1, s2)| s1 - pair.hedge_ratio * s2)
            .collect();

        let z_scores = calculate_zscore(&spread, args.window);
        let z_score = z_scores.last().copied().unwrap_or(f64::NAN);

        if z_score.is_nan() {
            continue;
        }

        // Check entry conditions
        if z_score.abs() >= args.zscore_threshold && pair.half_life <= args.half_life_threshold as f64 {
            // Check if already open
            if !is_open_position(&bot_agents, &pair.base_market)
                && !is_open_position(&bot_agents, &pair.quote_market)
            {
                // Determine side
                let base_side = if z_score < 0.0 { "BUY" } else { "SELL" };
                let quote_side = if z_score > 0.0 { "BUY" } else { "SELL" };

                // Get prices
                let base_price = series_1.last().copied().unwrap_or(0.0);
                let quote_price = series_2.last().copied().unwrap_or(0.0);

                // Calculate size
                let base_quantity = args.usd_per_trade / base_price;
                let quote_quantity = args.usd_per_trade / quote_price;
                let base_size = base_quantity as i32;
                let quote_size = quote_quantity as i32;

                if base_size >= 1 && quote_size >= 1 {
                    let market_1_cn = crate::commodity::get_contract_name(&pair.base_market)
                        .unwrap_or_else(|| pair.base_market.clone());
                    let market_2_cn = crate::commodity::get_contract_name(&pair.quote_market)
                        .unwrap_or_else(|| pair.quote_market.clone());

                    let bot_agent = BotAgent {
                        market_1: pair.base_market.clone(),
                        market_2: pair.quote_market.clone(),
                        market_1_cn,
                        market_2_cn,
                        hedge_ratio: pair.hedge_ratio,
                        z_score,
                        half_life: pair.half_life,
                        order_id_m1: String::new(),
                        order_m1_size: base_size.to_string(),
                        order_m1_side: base_side.to_string(),
                        order_time_m1: format!("{:?}", std::time::SystemTime::now()),
                        order_id_m2: String::new(),
                        order_m2_size: quote_size.to_string(),
                        order_m2_side: quote_side.to_string(),
                        order_time_m2: format!("{:?}", std::time::SystemTime::now()),
                        pair_status: "LIVE".to_string(),
                        comments: String::new(),
                    };

                    println!(
                        "Opened position: {}/{} (z_score: {:.2})",
                        pair.base_market, pair.quote_market, z_score
                    );
                    bot_agents.push(bot_agent);
                    new_positions += 1;
                }
            }
        }
    }

    // Save updated positions
    save_open_positions(&bot_agents_path, &bot_agents)?;
    println!("Success: {} New Pairs LIVE", new_positions);

    Ok(new_positions)
}
