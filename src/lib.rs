pub mod broker;
pub mod ibkr;
pub mod mock;
pub mod risk;
pub mod rebalancer;
pub mod execution_tests;

use pyo3::prelude::*;
use pyo3::types::PyDict;
use tokio::runtime::Runtime;
use crate::broker::Broker;
use crate::ibkr::{IbkrBroker, NewsHeadline};
use crate::mock::MockBroker;
use crate::risk::RiskManager;
use crate::rebalancer::{read_target_weights, HybridRebalancer};

use arrow::ffi::{FFI_ArrowArray, FFI_ArrowSchema, from_ffi};
use arrow::array::{Array, StringArray, Float64Array, StructArray};
use arrow::record_batch::RecordBatch;
use std::sync::Arc;
use dashmap::DashMap;

/// A high-performance execution engine that uses the Arrow C Data Interface
/// to receive zero-copy buffers from Python.
#[pyclass]
pub struct ExecutionEngine {
    pub risk_manager: Py<RiskManager>,
    pub broker: Option<Box<dyn Broker>>,
    pub rt: Runtime,
    pub latest_news: Arc<DashMap<String, Vec<String>>>,
}

#[pymethods]
impl ExecutionEngine {
    #[new]
    fn new(risk_manager: Py<RiskManager>) -> Self {
        ExecutionEngine { 
            risk_manager,
            broker: None,
            rt: Runtime::new().unwrap(),
            latest_news: Arc::new(DashMap::new()),
        }
    }

    /// Dynamically instantiates and connects a broker.
    fn set_broker(&mut self, broker_type: &str, config: &PyDict) -> PyResult<()> {
        match broker_type {
            "ibkr" => {
                let host: String = config.get_item("host")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("host missing"))?.extract()?;
                let port: u32 = config.get_item("port")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("port missing"))?.extract()?;
                let client_id: i32 = config.get_item("client_id")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("client_id missing"))?.extract()?;
                let api_token: Option<String> = config.get_item("api_token")?.map(|v| v.extract()).transpose()?;
                
                let mut broker = IbkrBroker::new(host, port, client_id, api_token);
                self.rt.block_on(broker.connect()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
                
                let news_tx = broker.news_sender.clone();
                let news_map = self.latest_news.clone();

                // Spawn the event loop to handle incoming messages
                if let Some(reader) = broker.take_reader() {
                    let id_arc = broker.next_order_id.clone();
                    let md_arc = broker.market_data.clone();
                    let res_arc = broker.account_responders.clone();
                    let ticker_map = broker.ticker_map.clone();
                    
                    self.rt.spawn(async move {
                        if let Err(e) = IbkrBroker::start_event_loop(reader, id_arc, md_arc, res_arc, news_tx, ticker_map).await {
                            eprintln!("IBKR Event Loop Error: {}", e);
                        }
                    });

                    // Also spawn a news listener to populate the shared map
                    let mut news_rx = broker.news_sender.subscribe();
                    self.rt.spawn(async move {
                        while let Ok(news) = news_rx.recv().await {
                            let mut list = news_map.entry(news.symbol.clone()).or_insert_with(Vec::new);
                            list.push(news.headline);
                            if list.len() > 10 { list.remove(0); } // Keep only last 10
                        }
                    });

                    println!("ExecutionEngine: IBKR event loop and news listener spawned.");
                }
                
                self.broker = Some(Box::new(broker));
                println!("ExecutionEngine: IBKR broker set and connected.");
            },
            "mock" => {
                let balance: f64 = config.get_item("balance")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("balance missing"))?.extract()?;
                let mut broker = MockBroker::new(balance);
                self.rt.block_on(broker.connect()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
                self.broker = Some(Box::new(broker));
                println!("ExecutionEngine: Mock broker set and connected.");
            },
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unknown broker type")),
        }
        Ok(())
    }

    /// Subscribes to news for a specific symbol.
    fn subscribe_news(&self, symbol: &str) -> PyResult<()> {
        let broker = self.broker.as_ref().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("No broker set"))?;
        self.rt.block_on(broker.subscribe_news(symbol))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    /// Fetches latest news for a symbol and clears the buffer.
    fn get_latest_news(&self, symbol: &str) -> PyResult<Vec<String>> {
        if let Some((_, news)) = self.latest_news.remove(symbol) {
            Ok(news)
        } else {
            Ok(vec![])
        }
    }

    /// Processes a batch of signals from Python using zero-copy Arrow RecordBatches.
    fn process_signals(&self, py: Python, array_ptr: usize, schema_ptr: usize) -> PyResult<()> {
        let array = unsafe { FFI_ArrowArray::from_raw(array_ptr as *mut _) };
        let schema = unsafe { FFI_ArrowSchema::from_raw(schema_ptr as *mut _) };

        let array_data = unsafe { from_ffi(array, &schema) }
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Arrow FFI Error: {}", e)))?;
        
        let struct_array = StructArray::from(array_data);
        let batch = RecordBatch::from(&struct_array);

        let mut rm = self.risk_manager.borrow_mut(py);
        self.process_batch(&batch, &mut rm)?;

        Ok(())
    }

    fn get_balance(&self) -> PyResult<f64> {
        let broker = self.broker.as_ref().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("No broker set"))?;
        self.rt.block_on(broker.get_account_balance())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    fn get_positions(&self) -> PyResult<std::collections::HashMap<String, f64>> {
        let broker = self.broker.as_ref().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("No broker set"))?;
        self.rt.block_on(broker.get_positions())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    fn run_rebalancing(&self, py: Python, ipc_path: &str, tolerance: f64) -> PyResult<()> {
        let broker = self.broker.as_ref().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("No broker set"))?;
        let mut rm = self.risk_manager.borrow_mut(py);
        
        let target_weights = read_target_weights(ipc_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
        
        let mut rebalancer = HybridRebalancer::new(broker.as_ref(), &mut rm, &self.rt);
        rebalancer.run_rebalancing_cycle(target_weights, tolerance)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
            
        Ok(())
    }
}

impl ExecutionEngine {
    fn process_batch(&self, batch: &RecordBatch, rm: &mut RiskManager) -> PyResult<()> {
        if rm.kill_switch_triggered {
            println!("ExecutionEngine: Kill switch is active. Ignoring signals.");
            return Ok(());
        }

        if let Some(ref broker) = self.broker {
            let symbols = batch.column_by_name("symbol")
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Column 'symbol' not found"))?
                .as_any().downcast_ref::<StringArray>()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Column 'symbol' is not a StringArray"))?;
            
            let signals = batch.column_by_name("signal")
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Column 'signal' not found"))?
                .as_any().downcast_ref::<Float64Array>()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Column 'signal' is not a Float64Array"))?;

            let prices = batch.column_by_name("price")
                .and_then(|col| col.as_any().downcast_ref::<Float64Array>());

            for i in 0..batch.num_rows() {
                if signals.is_null(i) { continue; }
                
                let symbol_str = symbols.value(i);
                let signal_val = signals.value(i);
                
                if signal_val != 0.0 {
                    let price = if let Some(p) = prices {
                        if p.is_null(i) { 50000.0 } else { p.value(i) }
                    } else {
                        50000.0
                    };
                    
                    let quantity = signal_val; 
                    
                    if rm.validate_order(symbol_str, quantity, price)? {
                        let result = self.rt.block_on(broker.place_order(symbol_str, quantity, price));
                        match result {
                            Ok(order_id) => {
                                println!("ExecutionEngine: Order placed successfully: {}", order_id);
                                rm.update_position(symbol_str, quantity, price);
                                rm.update_loss(10.0);
                            },
                            Err(e) => println!("ExecutionEngine: Order failed: {}", e),
                        }
                    }
                }
            }
        }
        Ok(())
    }
}

#[pyfunction]
fn get_version() -> String {
    "0.1.0".to_string()
}

#[pymodule]
fn _lib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RiskManager>()?;
    m.add_class::<ExecutionEngine>()?;
    m.add_class::<MockBroker>()?;
    m.add_function(wrap_pyfunction!(get_version, m)?)?;
    Ok(())
}
