use pyo3::prelude::*;
use std::collections::HashMap;
use std::time::{Instant, Duration};

#[pyclass]
pub struct RiskManager {
    #[pyo3(get, set)]
    pub max_exposure_per_symbol: f64,
    #[pyo3(get, set)]
    pub max_total_exposure: f64,
    #[pyo3(get, set)]
    pub drawdown_limit: f64,
    #[pyo3(get, set)]
    pub current_loss: f64,
    #[pyo3(get, set)]
    pub kill_switch_triggered: bool,
    
    // Order Velocity Safeguards
    #[pyo3(get, set)]
    pub max_orders_per_window: usize,
    #[pyo3(get, set)]
    pub velocity_window_seconds: u64,
    pub order_history: Vec<Instant>,
    
    // Internal state for exposure tracking
    pub positions: HashMap<String, f64>, // symbol -> quantity
    pub total_exposure: f64,
}

#[pymethods]
impl RiskManager {
    #[new]
    pub fn new(
        max_exposure_per_symbol: f64, 
        max_total_exposure: f64, 
        drawdown_limit: f64,
        max_orders_per_window: usize,
        velocity_window_seconds: u64,
    ) -> Self {
        RiskManager {
            max_exposure_per_symbol,
            max_total_exposure,
            drawdown_limit,
            current_loss: 0.0,
            kill_switch_triggered: false,
            max_orders_per_window,
            velocity_window_seconds,
            order_history: Vec::new(),
            positions: HashMap::new(),
            total_exposure: 0.0,
        }
    }

    /// Validates if an order can be placed based on risk limits.
    pub fn validate_order(&mut self, symbol: &str, quantity: f64, price: f64) -> PyResult<bool> {
        if self.kill_switch_triggered {
            println!("RiskManager: Validation failed - Kill switch is active.");
            return Ok(false);
        }

        // 1. Check Order Velocity
        let now = Instant::now();
        let window = Duration::from_secs(self.velocity_window_seconds);
        
        // Remove old entries
        self.order_history.retain(|&t| now.duration_since(t) < window);
        
        if self.order_history.len() >= self.max_orders_per_window {
            self.kill_switch_triggered = true;
            println!("RiskManager: KILL SWITCH TRIGGERED! Velocity limit reached: {} orders in {}s", 
                     self.order_history.len(), self.velocity_window_seconds);
            return Ok(false);
        }

        // 2. Check Exposure Limits
        let current_qty = self.positions.get(symbol).cloned().unwrap_or(0.0);
        let new_qty = current_qty + quantity;
        let new_exposure = new_qty.abs() * price;

        if new_exposure > self.max_exposure_per_symbol {
            println!("RiskManager: Validation failed - Max exposure per symbol exceeded for {}. ({} > {})", 
                     symbol, new_exposure, self.max_exposure_per_symbol);
            return Ok(false);
        }

        let current_exposure = current_qty.abs() * price;
        let new_total_exposure = self.total_exposure - current_exposure + new_exposure;

        if new_total_exposure > self.max_total_exposure {
            println!("RiskManager: Validation failed - Max total exposure exceeded. ({} > {})", 
                     new_total_exposure, self.max_total_exposure);
            return Ok(false);
        }

        // Log this validation as a potential order in the velocity history
        self.order_history.push(now);

        Ok(true)
    }

    pub fn update_position(&mut self, symbol: &str, quantity: f64, price: f64) {
        let current_qty = self.positions.get(symbol).cloned().unwrap_or(0.0);
        let current_exposure = current_qty.abs() * price;
        
        let new_qty = current_qty + quantity;
        let new_exposure = new_qty.abs() * price;
        
        self.total_exposure = self.total_exposure - current_exposure + new_exposure;
        self.positions.insert(symbol.to_string(), new_qty);
    }

    pub fn update_loss(&mut self, loss: f64) {
        self.current_loss += loss;
        if self.current_loss >= self.drawdown_limit {
            self.kill_switch_triggered = true;
            println!("RiskManager: KILL SWITCH TRIGGERED! Drawdown limit reached: {} >= {}", 
                     self.current_loss, self.drawdown_limit);
        }
    }

    pub fn reset_kill_switch(&mut self) {
        self.kill_switch_triggered = false;
        self.current_loss = 0.0;
        println!("RiskManager: Kill switch reset.");
    }
    
    #[getter]
    fn total_exposure(&self) -> f64 {
        self.total_exposure
    }
}
