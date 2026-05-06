import jegal
import pandas as pd
import numpy as np
from jegal.signals import generate_moving_average_signals
from jegal.engine_bridge import dispatch_to_execution_engine

def main():
    print(f"Starting Jegal System v{jegal.get_version()}...")

    # 1. Initialize Rust Components
    # Using conservative limits for simulation
    risk_manager = jegal.RiskManager(
        max_exposure_per_symbol=100000.0, 
        max_total_exposure=500000.0, 
        drawdown_limit=1000.0,
        max_orders_per_window=100,
        velocity_window_seconds=60
    )
    execution_engine = jegal.ExecutionEngine(risk_manager)
    print("Rust Execution Engine initialized with RiskManager.")

    # 2. Simulate Research Layer Data
    print("Generating simulated market data and signals...")
    data = {
        "symbol": ["BTC-USD"] * 1000,
        "close": np.random.uniform(60000, 65000, 1000).tolist()
    }
    df = pd.DataFrame(data)
    df_with_signals = generate_moving_average_signals(df, fast_window=10, slow_window=50)

    # 3. Dispatch to Rust
    print("Dispatching signals to Rust execution engine via Arrow bridge...")
    dispatch_to_execution_engine(df_with_signals, execution_engine)
    
    print("System run complete.")

if __name__ == "__main__":
    main()
