use async_trait::async_trait;
use pyo3::prelude::*;

#[cfg_attr(test, mockall::automock)]
#[async_trait]
pub trait Broker: Send + Sync {
    async fn connect(&mut self) -> Result<(), String>;
    async fn get_account_balance(&self) -> Result<f64, String>;
    async fn get_positions(&self) -> Result<std::collections::HashMap<String, f64>, String>;
    async fn get_price(&self, symbol: &str) -> Result<f64, String>;
    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String>;
}
