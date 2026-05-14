import pandas as pd

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators for ML feature engineering.
    """
    df = df.copy()
    
    # Placeholder indicators using pandas rolling windows
    df['macd_line'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['macd_signal'] = df['macd_line'].ewm(span=9).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Simple ADX proxy (rolling volatility)
    df['adx'] = df['close'].rolling(window=14).std()
    
    return df.dropna()
