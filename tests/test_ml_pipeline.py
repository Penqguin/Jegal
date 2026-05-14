import pandas as pd
import numpy as np
from jegal.ml_engine import MLEngine
from jegal.engine_bridge import write_target_weights
import jegal
import json

def run_pipeline():
    # 1. Simulate enough market data for 14-period indicators
    data = {
        'symbol': ['AAPL'] * 20,
        'close': np.random.rand(20) * 100 + 200,
        'high': np.random.rand(20) * 100 + 210,
        'low': np.random.rand(20) * 100 + 190
    }
    df = pd.DataFrame(data)
    
    # 2. Run ML Pipeline
    ml = MLEngine()
    target_weights_df = ml.generate_target_weights(df)
    print("Generated Target Weights:\n", target_weights_df)
    
    # 3. Dispatch to Rust via Arrow
    ipc_path = "/tmp/jegal_target_weights.arrow"
    write_target_weights(target_weights_df, ipc_path)
    print(f"Weights dispatched to {ipc_path}")

if __name__ == "__main__":
    run_pipeline()
