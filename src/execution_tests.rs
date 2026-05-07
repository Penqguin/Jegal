#[cfg(test)]
mod tests {
    use crate::*;
    use crate::broker::MockBroker as MockBrokerTrait; // This is the automocked trait
    use arrow_array::{StringArray, Float64Array};
    use arrow_schema::{Schema, Field, DataType};
    use arrow::record_batch::RecordBatch;
    use std::sync::Arc;
    use mockall::predicate::*;
    use pyo3::prelude::*;

    fn create_test_batch(symbol: &str, signal: f64, price: f64) -> RecordBatch {
        let schema = Arc::new(Schema::new(vec![
            Field::new("symbol", DataType::Utf8, false),
            Field::new("signal", DataType::Float64, false),
            Field::new("price", DataType::Float64, false),
        ]));

        let symbols = StringArray::from(vec![symbol]);
        let signals = Float64Array::from(vec![signal]);
        let prices = Float64Array::from(vec![price]);

        RecordBatch::try_new(
            schema,
            vec![
                Arc::new(symbols),
                Arc::new(signals),
                Arc::new(prices),
            ],
        ).unwrap()
    }

    #[test]
    fn test_buy_signal_fires_order() {
        let mut rm = RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60);
        let mut engine = Python::with_gil(|py| {
            let rm_py = Py::new(py, RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60)).unwrap();
            ExecutionEngine::new(rm_py)
        });

        let mut mock_broker = MockBrokerTrait::new();
        mock_broker.expect_place_order()
            .with(eq("AAPL"), eq(1.0), eq(300.0))
            .times(1)
            .returning(|_, _, _| Ok("ORDER-123".to_string()));

        engine.broker = Some(Box::new(mock_broker));
        
        let batch = create_test_batch("AAPL", 1.0, 300.0);
        let result = engine.process_batch(&batch, &mut rm);
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_hold_signal_does_not_fire_order() {
        let mut rm = RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60);
        let mut engine = Python::with_gil(|py| {
            let rm_py = Py::new(py, RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60)).unwrap();
            ExecutionEngine::new(rm_py)
        });

        let mut mock_broker = MockBrokerTrait::new();
        mock_broker.expect_place_order()
            .times(0);

        engine.broker = Some(Box::new(mock_broker));
        
        let batch = create_test_batch("AAPL", 0.0, 300.0);
        let result = engine.process_batch(&batch, &mut rm);
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_risk_management_kill_switch_blocks_order() {
        let mut rm = RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60);
        rm.kill_switch_triggered = true; // Manually trigger kill switch

        let mut engine = Python::with_gil(|py| {
            let rm_py = Py::new(py, RiskManager::new(100000.0, 500000.0, 1000.0, 10, 60)).unwrap();
            ExecutionEngine::new(rm_py)
        });

        let mut mock_broker = MockBrokerTrait::new();
        mock_broker.expect_place_order()
            .times(0);

        engine.broker = Some(Box::new(mock_broker));
        
        let batch = create_test_batch("AAPL", 1.0, 300.0);
        let result = engine.process_batch(&batch, &mut rm);
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_risk_management_exposure_limit_blocks_order() {
        // Limit of 100.0, but order is 1.0 * 150.0 = 150.0
        let mut rm = RiskManager::new(100.0, 500.0, 1000.0, 10, 60);

        let mut engine = Python::with_gil(|py| {
            let rm_py = Py::new(py, RiskManager::new(100.0, 500.0, 1000.0, 10, 60)).unwrap();
            ExecutionEngine::new(rm_py)
        });

        let mut mock_broker = MockBrokerTrait::new();
        mock_broker.expect_place_order()
            .times(0);

        engine.broker = Some(Box::new(mock_broker));
        
        let batch = create_test_batch("AAPL", 1.0, 300.0);
        let result = engine.process_batch(&batch, &mut rm);
        
        assert!(result.is_ok());
        // Verify position wasn't updated
        assert_eq!(rm.total_exposure, 0.0);
    }
}
