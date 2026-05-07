use crate::broker::Broker;
use async_trait::async_trait;
use pyo3::prelude::*;

/// A mock broker for testing and simulation.
/// Implements the Broker trait to simulate successful interactions.
#[pyclass]
#[derive(Clone)]
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

    fn get_price(&self, symbol: String) -> PyResult<f64> {
        let mut rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(self.get_price_async(&symbol)).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }
    
    fn place_order(&self, symbol: String, quantity: f64, price: f64) -> PyResult<String> {
        let mut rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(self.place_order_async(&symbol, quantity, price)).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }
}

// Rename async methods to avoid conflict
impl MockBroker {
    async fn get_price_async(&self, symbol: &str) -> Result<f64, String> {
        println!("MockBroker: Simulating price for {}", symbol);
        Ok(100.0)
    }
    
    async fn place_order_async(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String> {
        println!("MockBroker: Simulating order for {} @ {} (Qty: {})", symbol, price, quantity);
        Ok(format!("MOCK-ORD-{}", symbol))
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

    async fn get_positions(&self) -> Result<std::collections::HashMap<String, f64>, String> {
        println!("MockBroker: Fetching simulated positions (empty).");
        Ok(std::collections::HashMap::new())
    }

    async fn get_price(&self, symbol: &str) -> Result<f64, String> {
        self.get_price_async(symbol).await
    }

    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String> {
        self.place_order_async(symbol, quantity, price).await
    }
}
