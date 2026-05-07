import jegal
import pandas as pd
from jegal.engine_bridge import dispatch_to_execution_engine

def test_ibkr_connection():
    """
    Test script for connecting Jegal to IBKR Desktop (Paper Trading).
    """
    print("--- IBKR Connectivity Test ---")
    
    # 1. Initialize Risk Manager with tight limits for testing
    risk_manager = jegal.RiskManager(
        max_exposure_per_symbol=5000.0, 
        max_total_exposure=10000.0, 
        drawdown_limit=100.0,
        max_orders_per_window=5,
        velocity_window_seconds=60
    )
    
    # 2. Initialize Execution Engine
    engine = jegal.ExecutionEngine(risk_manager)
    
    # 3. Configure IBKR Connection
    # Default IBKR Paper Trading port is 7497 (TWS) or 4002 (IB Gateway)
    # IBKR Desktop often uses 7497. Check your API settings!
    ibkr_config = {
        "host": "127.0.0.1",
        "port": 4002, # 7497 is the default for TWS Paper Trading
        "client_id": 99,
    }

    
    try:
        print(f"Connecting to IBKR at {ibkr_config['host']}:{ibkr_config['port']}...")
        engine.set_broker("ibkr", ibkr_config)
        print("Successfully connected to IBKR!")
        
        # Give the event loop a moment to receive the 'Next Valid ID' from the server
        import time
        print("Syncing with server...")
        time.sleep(2)
        
    except Exception as e:
        print(f"Failed to connect to IBKR: {e}")
        print("Ensure IBKR Desktop is open and 'Enable ActiveX and Socket Clients' is checked.")
        return

    # 4. Send a small test signal (e.g., Buy 1 share of AAPL if price is low)
    # NOTE: This will attempt to place a real order on your Paper Trading account.
    print("\nSending test signal for 1 share of AAPL...")
    test_df = pd.DataFrame({
        'symbol': ['AAPL'],
        'signal': [1.0],
        'price': [300.0]  # This is a limit price
    })
    
    dispatch_to_execution_engine(test_df, engine)
    
    import time
    print("\nWaiting 5 seconds for IBKR to process the order...")
    time.sleep(5)
    
    print("\nTest complete. Check your IBKR Desktop 'Orders' tab.")

if __name__ == "__main__":
    test_ibkr_connection()
