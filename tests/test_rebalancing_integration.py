import pytest
import pandas as pd
import os
import jegal
from jegal.engine_bridge import write_target_weights

def test_rebalancing_flow():
    # 1. Setup Mock Data
    ipc_path = "/tmp/test_target_weights.arrow"
    data = {
        "ticker": ["BTC-USD", "ETH-USD"],
        "weight": [0.6, 0.4]
    }
    df = pd.DataFrame(data)
    write_target_weights(df, ipc_path)

    # 2. Setup Engine
    risk_manager = jegal.RiskManager(
        max_exposure_per_symbol=1000000.0,
        max_total_exposure=2000000.0,
        drawdown_limit=10000.0,
        max_orders_per_window=100,
        velocity_window_seconds=60
    )
    engine = jegal.ExecutionEngine(risk_manager)
    engine.set_broker("mock", {"balance": 100000.0})

    # 3. Run Rebalancing
    # This should trigger trades for BTC-USD (60,000) and ETH-USD (40,000) 
    # since current positions are zero and tolerance is 0.05
    engine.run_rebalancing(ipc_path, tolerance=0.05)
    
    # 4. Cleanup
    if os.path.exists(ipc_path):
        os.remove(ipc_path)

if __name__ == "__main__":
    test_rebalancing_flow()
