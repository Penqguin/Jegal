import pytest
import pandas as pd
import numpy as np
import jegal

def test_full_integration():
    """
    Performs a full end-to-end test of the Jegal system.
    1. Initialize MockBroker and RiskManager.
    2. Setup ExecutionEngine with MockBroker.
    3. Generate signals from sample data.
    4. Process signals through the engine.
    5. Verify order execution and risk tracking.
    """
    # 1. Initialize MockBroker and RiskManager
    mock_balance = 100000.0
    max_exposure_per_symbol = 60000.0
    max_total_exposure = 150000.0
    drawdown_limit = 1000.0
    max_orders_per_window = 10
    velocity_window_seconds = 60
    
    risk_manager = jegal.RiskManager(
        max_exposure_per_symbol, 
        max_total_exposure, 
        drawdown_limit,
        max_orders_per_window,
        velocity_window_seconds
    )
    
    # 2. Setup ExecutionEngine
    engine = jegal.ExecutionEngine(risk_manager)
    engine.set_broker("mock", {"balance": mock_balance})
    
    # 3. Generate signals
    # BTC at 50000, 1.0 signal -> 50000 exposure
    # ETH at 50000, -1.0 signal -> 50000 exposure (absolute value)
    df = pd.DataFrame({
        "symbol": ["BTC-USD", "ETH-USD"],
        "signal": [1.0, -1.0],
        "price": [50000.0, 50000.0]
    })
    df["symbol"] = df["symbol"].astype(str)
    
    # 4. Process signals
    from jegal.engine_bridge import dispatch_to_execution_engine
    dispatch_to_execution_engine(df, engine)
    
    # 5. Verify results
    # Each successful order updates loss by 10.0 in our simulation
    assert risk_manager.current_loss == 20.0
    assert risk_manager.total_exposure == 100000.0
    assert not risk_manager.kill_switch_triggered
    
    # Test Exposure Limit per Symbol
    # Adding 0.5 BTC will bring BTC exposure to 1.5 * 50000 = 75000, which exceeds 60000
    btc_df = pd.DataFrame({
        "symbol": ["BTC-USD"],
        "signal": [0.5],
        "price": [50000.0]
    })
    dispatch_to_execution_engine(btc_df, engine)
    # Exposure should NOT have changed
    assert risk_manager.total_exposure == 100000.0
    assert risk_manager.current_loss == 20.0
    
    # Test Total Exposure Limit
    # Max total is 150000. Current is 100000.
    # Add LTC at 50000, 1.5 units -> 75000 exposure. Total would be 175000.
    ltc_df = pd.DataFrame({
        "symbol": ["LTC-USD"],
        "signal": [1.5],
        "price": [50000.0]
    })
    dispatch_to_execution_engine(ltc_df, engine)
    assert risk_manager.total_exposure == 100000.0
    
    # Test Kill Switch (Velocity Limit)
    # The max_orders_per_window is 10. We already placed orders in the setup (2).
    # We need 8 more orders to hit 10 total.
    for _ in range(9):
        velocity_df = pd.DataFrame({
            "symbol": ["BTC-USD"],
            "signal": [0.001],
            "price": [1.0]
        })
        dispatch_to_execution_engine(velocity_df, engine)
    
    assert risk_manager.kill_switch_triggered
    
    # Subsequent signals should be ignored
    current_loss_before = risk_manager.current_loss
    single_df = pd.DataFrame({"symbol": ["BTC-USD"], "signal": [0.001], "price": [1.0]})
    dispatch_to_execution_engine(single_df, engine)
    assert risk_manager.current_loss == current_loss_before

def test_mock_broker_direct():
    """Tests the MockBroker class directly."""
    broker = jegal.MockBroker(50000.0)
    assert broker.balance == 50000.0
    broker.balance = 60000.0
    assert broker.balance == 60000.0
