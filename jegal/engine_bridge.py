import pyarrow as pa
import pandas as pd
import ctypes
from ._lib import RiskManager, ExecutionEngine

def dispatch_to_execution_engine(df: pd.DataFrame, engine: ExecutionEngine):
    """
    Orchestrates the transfer of signal data to the Rust execution engine.
    
    This function converts Pandas data into Apache Arrow buffers for zero-copy 
    sharing across the Python/Rust boundary using the C Data Interface.
    
    Args:
        df (pd.DataFrame): DataFrame containing signals and market data.
        engine (ExecutionEngine): The instantiated Rust ExecutionEngine.
    """
    # 1. Ensure required columns exist
    if 'symbol' not in df.columns:
        df = df.copy()
        df['symbol'] = "SIMULATED_ASSET"
    
    # 2. Convert to Arrow Table with explicit schema for critical columns
    schema = pa.schema([
        ('symbol', pa.string()),
        ('signal', pa.float64()),
        ('price', pa.float64())
    ])
    
    # Filter df to match schema columns (handle optional price)
    cols = ['symbol', 'signal']
    if 'price' in df.columns:
        cols.append('price')
    
    # Forcing types
    table = pa.Table.from_pandas(df[cols], schema=schema if 'price' in df.columns else pa.schema([('symbol', pa.string()), ('signal', pa.float64())]))
    
    # 3. Export to Arrow Record Batches and pass to Rust zero-copy
    batches = table.to_batches()
    
    print(f"Orchestrating zero-copy dispatch for {len(batches)} record batches...")
    
    for batch in batches:
        # Allocate memory for Arrow C Data Interface structures
        # ArrowSchema is 72 bytes, ArrowArray is 80 bytes
        c_schema_buffer = ctypes.create_string_buffer(72)
        c_array_buffer = ctypes.create_string_buffer(80)
        
        c_schema_ptr = ctypes.addressof(c_schema_buffer)
        c_array_ptr = ctypes.addressof(c_array_buffer)
        
        # Export the batch to the C structures
        batch._export_to_c(c_array_ptr, c_schema_ptr)
        
        # Pass the pointers to the Rust engine
        engine.process_signals(c_array_ptr, c_schema_ptr)

def wrap_arrow_buffer(table: pa.Table) -> bytes:
    """
    Serializes an Arrow table into a buffer that can be shared.
    
    Args:
        table (pa.Table): The Arrow table to serialize.
        
    Returns:
        bytes: The serialized Arrow buffer.
    """
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()
