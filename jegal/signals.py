import numpy as np
import pandas as pd
from typing import Tuple

def generate_moving_average_signals(
    df: pd.DataFrame, 
    fast_window: int = 50, 
    slow_window: int = 200
) -> pd.DataFrame:
    """
    Generates trading signals based on a simple moving average crossover strategy.
    
    Args:
        df (pd.DataFrame): DataFrame containing at least a 'close' price column.
        fast_window (int): Period for the fast moving average. Defaults to 50.
        slow_window (int): Period for the slow moving average. Defaults to 200.
        
    Returns:
        pd.DataFrame: Original DataFrame with added 'fast_ma', 'slow_ma', and 'signal' columns.
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column for signal generation.")

    # Calculate moving averages using numpy/pandas
    df['fast_ma'] = df['close'].rolling(window=fast_window).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_window).mean()

    # Generate signals: 1 for buy (fast > slow), -1 for sell (fast < slow), 0 otherwise
    # We use np.where for vectorized performance
    df['signal'] = 0.0
    df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1.0
    df.loc[df['fast_ma'] < df['slow_ma'], 'signal'] = -1.0
    
    return df
