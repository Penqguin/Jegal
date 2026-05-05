use pyo3::prelude::*;

#[pyclass]
pub struct RiskManager {
    #[pyo3(get, set)]
    pub max_daily_loss: f64,
    #[pyo3(get, set)]
    pub current_loss: f64,
    #[pyo3(get, set)]
    pub kill_switch_triggered: bool,
}

#[pymethods]
impl RiskManager {
    #[new]
    fn new(max_daily_loss: f64) -> Self {
        RiskManager {
            max_daily_loss,
            current_loss: 0.0,
            kill_switch_triggered: false,
        }
    }

    fn check_risk(&mut self, potential_loss: f64) -> PyResult<bool> {
        if self.kill_switch_triggered {
            return Ok(false);
        }

        if (self.current_loss + potential_loss) > self.max_daily_loss {
            self.kill_switch_triggered = true;
            return Ok(false);
        }

        Ok(true)
    }

    fn update_loss(&mut self, loss: f64) {
        self.current_loss += loss;
        if self.current_loss > self.max_daily_loss {
            self.kill_switch_triggered = true;
        }
    }
}

#[pyfunction]
fn get_version() -> String {
    "0.1.0".to_string()
}

#[pymodule]
fn _lib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RiskManager>()?;
    m.add_function(wrap_pyfunction!(get_version, m)?)?;
    Ok(())
}
