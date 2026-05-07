import pytest
import pandas as pd
import pyarrow as pa
from jegal._lib import RiskManager, ExecutionEngine
from jegal.engine_bridge import dispatch_to_execution_engine

def test_bridge_buy_signal_handoff():
    """
    Verifies the full handoff from a Python DataFrame to the Rust ExecutionEngine.
    """
    # 1. Setup RiskManager and Engine
    # RiskManager(max_symbol, max_total, drawdown, max_orders, window)
    rm = RiskManager(100000.0, 500000.0, 1000.0, 10, 60)
    engine = ExecutionEngine(rm)
    
    # 2. Set a mock broker in the engine
    # Our Rust engine's set_broker("mock", ...) method expects a balance
    engine.set_broker("mock", {"balance": 1000000.0})
    
    # 3. Create a 'BUY' signal DataFrame
    data = {
        'symbol': ['AAPL', 'TSLA'],
        'signal': [1.0, 0.0], # AAPL Buy, TSLA Hold
        'price': [150.0, 200.0]
    }
    df = pd.DataFrame(data)
    
    # 4. Dispatch to Rust
    # This should call process_signals in Rust zero-copy
    dispatch_to_execution_engine(df, engine)
    
    # 5. Assertions
    # If successful, AAPL should have been "executed" and exposure updated.
    # In our Rust code, rm.update_position is called on success.
    assert rm.total_exposure == 1.0 * 150.0
    
    # Verify TSLA (signal 0.0) did not add to exposure
    # (Since total_exposure is sum of all positions)
    # Note: total_exposure is a property/getter in Rust
    
    # 6. Test Sell signal
    sell_df = pd.DataFrame({
        'symbol': ['AAPL'],
        'signal': [-1.0],
        'price': [150.0]
    })
    dispatch_to_execution_engine(sell_df, engine)
    
    # After selling 1.0 AAPL (had 1.0) @ 150.0, position should be 0.0
    # Exposure = 150.0 - (1.0 * 150.0) + (0.0 * 150.0) = 0.0
    assert rm.total_exposure == 0.0

def test_bridge_kill_switch_trigger():
    """
    Verifies that the kill switch triggered in Rust is respected when signals are sent from Python.
    """
    rm = RiskManager(100000.0, 500000.0, 100.0, 10, 60)
    engine = ExecutionEngine(rm)
    engine.set_broker("mock", {"balance": 1000000.0})
    
    # Trigger kill switch manually
    rm.update_loss(150.0) 
    assert rm.kill_switch_triggered == True
    
    # Attempt a BUY signal
    df = pd.DataFrame({'symbol': ['AAPL'], 'signal': [1.0], 'price': [150.0]})
    dispatch_to_execution_engine(df, engine)
    
    # Exposure should still be 0.0
    assert rm.total_exposure == 0.0
