use async_trait::async_trait;
use pyo3::prelude::*;

#[async_trait]
pub trait Broker: Send + Sync {
    async fn connect(&mut self) -> Result<(), String>;
    async fn get_account_balance(&self) -> Result<f64, String>;
    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String>;
}
