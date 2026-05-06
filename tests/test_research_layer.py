import pytest
import pandas as pd
import numpy as np
import os
from jegal.data_loader import load_market_data
from jegal.signals import generate_moving_average_signals

@pytest.fixture
def sample_csv(tmp_path):
    """Creates a temporary CSV file for testing data ingestion."""
    csv_file = tmp_path / "test_data.csv"
    data = {
        "timestamp": ["2026-05-01", "2026-05-02", "2026-05-03"],
        "close": [100.0, 110.0, 105.0],
        "volume": [1000, 1500, 1200]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    return str(csv_file)

def test_data_loader(sample_csv):
    """Verifies that data is loaded correctly with Arrow-backed types."""
    df = load_market_data(sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert 'close' in df.columns
    # Check if we are using arrow-backed types (optional but good for validation)
    assert any(str(dtype).endswith('[pyarrow]') for dtype in df.dtypes)

def test_signal_generation():
    """Tests the moving average crossover signal logic."""
    data = {
        "close": np.linspace(100, 200, 300) # Prices steadily increasing
    }
    df = pd.DataFrame(data)
    
    # Fast = 10, Slow = 50. Since prices increase, fast should cross above slow.
    df_signals = generate_moving_average_signals(df, fast_window=10, slow_window=50)
    
    assert 'fast_ma' in df_signals.columns
    assert 'slow_ma' in df_signals.columns
    assert 'signal' in df_signals.columns
    
    # After slow_window is reached, signal should be 1.0 (buy) because prices are rising
    assert df_signals['signal'].iloc[-1] == 1.0

def test_signal_generation_value_error():
    """Ensures a ValueError is raised if 'close' column is missing."""
    df = pd.DataFrame({"price": [100, 110]})
    with pytest.raises(ValueError, match="DataFrame must contain a 'close' column"):
        generate_moving_average_signals(df)
