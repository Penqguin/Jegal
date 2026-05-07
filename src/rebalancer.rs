use arrow::record_batch::RecordBatch;
use arrow::ipc::reader::StreamReader;
use arrow::array::{StringArray, Float64Array};
use std::fs::File;
use std::io::BufReader;
use std::collections::HashMap;
use crate::broker::Broker;
use crate::risk::RiskManager;
use tokio::runtime::Runtime;

pub struct HybridRebalancer<'a> {
    pub broker: &'a dyn Broker,
    pub risk_manager: &'a mut RiskManager,
    pub rt: &'a Runtime,
}

impl<'a> HybridRebalancer<'a> {
    pub fn new(broker: &'a dyn Broker, risk_manager: &'a mut RiskManager, rt: &'a Runtime) -> Self {
        Self { broker, risk_manager, rt }
    }

    pub fn run_rebalancing_cycle(&mut self, target_weights: RecordBatch, tolerance: f64) -> Result<(), String> {
        if self.risk_manager.kill_switch_triggered {
            return Err("Rebalancer: Kill switch is active. Aborting.".to_string());
        }

        // 1. Fetch current balance and positions
        let balance = self.rt.block_on(self.broker.get_account_balance())?;
        let positions = self.rt.block_on(self.broker.get_positions())?;

        // 2. Parse target weights from Arrow
        let tickers = target_weights.column_by_name("ticker")
            .ok_or("Column 'ticker' not found")?
            .as_any().downcast_ref::<StringArray>()
            .ok_or("Column 'ticker' is not a StringArray")?;
        
        let weights = target_weights.column_by_name("weight")
            .ok_or("Column 'weight' not found")?
            .as_any().downcast_ref::<Float64Array>()
            .ok_or("Column 'weight' is not a Float64Array")?;

        let mut target_map = HashMap::new();
        for i in 0..target_weights.num_rows() {
            target_map.insert(tickers.value(i).to_string(), weights.value(i));
        }

        // 3. Identify all assets (current + target)
        let mut all_assets: std::collections::HashSet<String> = positions.keys().cloned().collect();
        for ticker in target_map.keys() {
            all_assets.insert(ticker.clone());
        }

        // 4. Calculate trades
        let mut trades = Vec::new();
        for asset in all_assets {
            let target_weight = target_map.get(&asset).cloned().unwrap_or(0.0);
            
            // Fetch live price for accurate valuation
            let price = self.rt.block_on(self.broker.get_price(&asset)).unwrap_or(1.0);
            
            let current_qty = positions.get(&asset).cloned().unwrap_or(0.0);
            let current_value = current_qty * price;
            let total_value = balance + positions.iter().map(|(sym, qty)| {
                let p = self.rt.block_on(self.broker.get_price(sym)).unwrap_or(1.0);
                qty * p
            }).sum::<f64>();

            let current_weight = if total_value > 0.0 { current_value / total_value } else { 0.0 };
            
            let deviation = (target_weight - current_weight).abs();
            if deviation > tolerance {
                let target_value = target_weight * total_value;
                let trade_qty = (target_value - current_value) / price;
                trades.push((asset, trade_qty, price));
            }
        }

        // 5. Execute trades: Sell first to generate cash
        trades.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

        for (asset, qty, price) in trades {
            if qty.abs() < 0.0001 { continue; }
            
            // Risk Check
            if self.risk_manager.validate_order(&asset, qty, price).map_err(|e| e.to_string())? {
                println!("Rebalancer: Executing trade for {}: Qty {} @ {}", asset, qty, price);
                let result = self.rt.block_on(self.broker.place_order(&asset, qty, price));
                match result {
                    Ok(order_id) => {
                        println!("Rebalancer: Order successful: {}", order_id);
                        self.risk_manager.update_position(&asset, qty, price);
                    },
                    Err(e) => println!("Rebalancer: Order failed: {}", e),
                }
            } else {
                println!("Rebalancer: Risk check failed for {}. Skipping.", asset);
            }
        }

        Ok(())
    }
}

pub fn read_target_weights(path: &str) -> Result<RecordBatch, String> {
    let file = File::open(path).map_err(|e| format!("Failed to open Arrow file: {}", e))?;
    let reader = BufReader::new(file);
    let mut stream_reader = StreamReader::try_new(reader, None)
        .map_err(|e| format!("Failed to create Arrow stream reader: {}", e))?;

    if let Some(maybe_batch) = stream_reader.next() {
        maybe_batch.map_err(|e| format!("Failed to read Arrow batch: {}", e))
    } else {
        Err("Arrow IPC stream is empty".to_string())
    }
}
