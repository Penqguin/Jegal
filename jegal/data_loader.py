import pandas as pd
import pyarrow as pa
from typing import Optional

def load_market_data(file_path: str) -> pd.DataFrame:
    """
    Loads historical market data from a CSV file into a Pandas DataFrame.
    
    Uses Apache Arrow-backed data types for memory efficiency and high performance.
    
    Args:
        file_path (str): Path to the CSV file containing OHLCV data.
        
    Returns:
        pd.DataFrame: A DataFrame with Arrow-backed types.
    """
    # Using 'pyarrow' as the engine and dtype_backend for optimal performance
    df = pd.read_csv(
        file_path, 
        engine='pyarrow', 
        dtype_backend='pyarrow'
    )
    
    # Ensure timestamp is parsed if it exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    return df

def df_to_arrow_table(df: pd.DataFrame) -> pa.Table:
    """
    Converts a Pandas DataFrame to an Apache Arrow Table for zero-copy transfer.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        
    Returns:
        pa.Table: The converted Arrow Table.
    """
    return pa.Table.from_pandas(df)
