use crate::broker::Broker;
use async_trait::async_trait;
use pyo3::prelude::*;

/// A mock broker for testing and simulation.
/// Implements the Broker trait to simulate successful interactions.
#[pyclass]
pub struct MockBroker {
    #[pyo3(get, set)]
    pub balance: f64,
}

#[pymethods]
impl MockBroker {
    #[new]
    pub fn new(balance: f64) -> Self {
        MockBroker { balance }
    }
}

#[async_trait]
impl Broker for MockBroker {
    async fn connect(&mut self) -> Result<(), String> {
        println!("MockBroker: Connection simulated.");
        Ok(())
    }

    async fn get_account_balance(&self) -> Result<f64, String> {
        println!("MockBroker: Fetching simulated balance: {}", self.balance);
        Ok(self.balance)
    }

    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String> {
        println!("MockBroker: Simulating order for {} @ {} (Qty: {})", symbol, price, quantity);
        Ok(format!("MOCK-ORD-{}", symbol))
    }
}
