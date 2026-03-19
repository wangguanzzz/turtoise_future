//! Exit logic for pair trading

use crate::config::Args;
use crate::data::MarketPrices;
use crate::strategies::cointegration::calculate_zscore;
use crate::strategies::entry::{load_open_positions, save_open_positions};
use std::path::Path;

/// Manage exiting open positions based on exit rules
pub fn manage_trade_exits(
    args: &Args,
    bot_agents_path: &Path,
    prices: &MarketPrices,
) -> Result<String, String> {
    let open_positions = load_open_positions(bot_agents_path);

    if open_positions.is_empty() {
        return Ok("complete".to_string());
    }

    let mut save_output = Vec::new();

    for position in &open_positions {
        let mut is_close = false;

        let series_1 = prices.get_series(&position.market_1);
        let series_2 = prices.get_series(&position.market_2);

        if args.close_at_zscore_cross {
            let hedge_ratio = position.hedge_ratio;
            let z_score_traded = position.z_score;

            if !series_1.is_empty() && series_1.len() == series_2.len() {
                let spread: Vec<f64> = series_1
                    .iter()
                    .zip(series_2.iter())
                    .map(|(s1, s2)| s1 - hedge_ratio * s2)
                    .collect();

                let z_scores = calculate_zscore(&spread, args.window);
                let z_score_current = z_scores.last().copied().unwrap_or(f64::NAN);

                if !z_score_current.is_nan() {
                    let z_score_level_check = z_score_current.abs() > args.zscore_threshold;
                    let z_score_cross_check = (z_score_current < 0.0 && z_score_traded > 0.0)
                        || (z_score_current > 0.0 && z_score_traded < 0.0);

                    if z_score_level_check && z_score_cross_check {
                        is_close = true;
                    }
                }
            }
        }

        if is_close {
            // In a real implementation, this would place closing orders
            // For now, we just log the exit
            println!(
                "Closing position: {}/{}",
                position.market_1, position.market_2
            );
        } else {
            save_output.push(position.clone());
        }
    }

    println!("{} Items remaining. Saving file ...", save_output.len());
    save_open_positions(bot_agents_path, &save_output)?;

    Ok("complete".to_string())
}
