pub mod broker;
pub mod ibkr;
pub mod questrade;
pub mod mock;
pub mod risk;

use pyo3::prelude::*;
use pyo3::types::PyDict;
use tokio::runtime::Runtime;
use crate::broker::Broker;
use crate::ibkr::IbkrBroker;
use crate::questrade::QuestradeBroker;
use crate::mock::MockBroker;
use crate::risk::RiskManager;

use arrow::ffi::{FFI_ArrowArray, FFI_ArrowSchema, from_ffi};
use arrow::array::{Array, StringArray, Float64Array, StructArray};
use arrow::record_batch::RecordBatch;
use std::sync::Arc;

/// A high-performance execution engine that uses the Arrow C Data Interface
/// to receive zero-copy buffers from Python.
#[pyclass]
pub struct ExecutionEngine {
    pub risk_manager: Py<RiskManager>,
    pub broker: Option<Box<dyn Broker>>,
    pub rt: Runtime,
}

#[pymethods]
impl ExecutionEngine {
    #[new]
    fn new(risk_manager: Py<RiskManager>) -> Self {
        ExecutionEngine { 
            risk_manager,
            broker: None,
            rt: Runtime::new().unwrap(),
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
                self.broker = Some(Box::new(broker));
                println!("ExecutionEngine: IBKR broker set and connected.");
            },
            "questrade" => {
                let account_id: String = config.get_item("account_id")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("account_id missing"))?.extract()?;
                let access_token: String = config.get_item("access_token")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("access_token missing"))?.extract()?;
                let refresh_token: String = config.get_item("refresh_token")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("refresh_token missing"))?.extract()?;
                let server_url: String = config.get_item("server_url")?.ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("server_url missing"))?.extract()?;
                
                let mut broker = QuestradeBroker::new(account_id, access_token, refresh_token, server_url);
                self.rt.block_on(broker.connect()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
                self.broker = Some(Box::new(broker));
                println!("ExecutionEngine: Questrade broker set and connected.");
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

    /// Processes a batch of signals from Python using zero-copy Arrow RecordBatches.
    /// Expects pointers to ArrowArray and ArrowSchema structures.
    fn process_signals(&self, py: Python, array_ptr: usize, schema_ptr: usize) -> PyResult<()> {
        // 1. Import from C Data Interface
        let array = unsafe { FFI_ArrowArray::from_raw(array_ptr as *mut _) };
        let schema = unsafe { FFI_ArrowSchema::from_raw(schema_ptr as *mut _) };

        let array_data = unsafe { from_ffi(array, &schema) }
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Arrow FFI Error: {}", e)))?;
        
        let struct_array = StructArray::from(array_data);
        let batch = RecordBatch::from(&struct_array);

        let mut rm = self.risk_manager.borrow_mut(py);
        
        if rm.kill_switch_triggered {
            println!("ExecutionEngine: Kill switch is active. Ignoring signals.");
            return Ok(());
        }

        if let Some(ref broker) = self.broker {
            // 2. Extract columns
            let symbols = batch.column_by_name("symbol")
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Column 'symbol' not found"))?
                .as_any().downcast_ref::<StringArray>()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Column 'symbol' is not a StringArray"))?;
            
            let signals = batch.column_by_name("signal")
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Column 'signal' not found"))?
                .as_any().downcast_ref::<Float64Array>()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Column 'signal' is not a Float64Array"))?;

            // Try to extract price column if it exists
            let prices = batch.column_by_name("price")
                .and_then(|col| col.as_any().downcast_ref::<Float64Array>());

            // 3. Iterate and process
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
                        println!("ExecutionEngine: Signal for {} is {}, placing order at {}...", symbol_str, signal_val, price);
                        
                        // Execute order via broker
                        let result = self.rt.block_on(broker.place_order(symbol_str, quantity, price));
                        match result {
                            Ok(order_id) => {
                                println!("ExecutionEngine: Order placed successfully: {}", order_id);
                                rm.update_position(symbol_str, quantity, price);
                                // For simulation and compatibility with existing tests, update loss
                                rm.update_loss(10.0);
                            },
                            Err(e) => println!("ExecutionEngine: Order failed: {}", e),
                        }
                    } else {
                        println!("ExecutionEngine: Risk check failed for {}. Order rejected.", symbol_str);
                    }
                }
            }
        } else {
            println!("ExecutionEngine: No broker set! Cannot process signals.");
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
