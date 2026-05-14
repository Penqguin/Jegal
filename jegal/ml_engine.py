import pandas as pd
import numpy as np
import xgboost as xgb
import tensorflow as tf
from jegal.feature_engineering import calculate_technical_indicators

class MLEngine:
    def __init__(self):
        self.xgb_model = xgb.XGBClassifier()
        # Placeholder for LSTM architecture
        self.lstm_model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, activation='relu', input_shape=(10, 5)),
            tf.keras.layers.Dense(1)
        ])
        # Dummy fit for prototype
        dummy_X = np.zeros((10, 4))
        dummy_y = np.zeros(10)
        self.xgb_model.fit(dummy_X, dummy_y)

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return calculate_technical_indicators(df)

    def predict_direction(self, df: pd.DataFrame) -> np.ndarray:
        features = self.prepare_features(df)
        # Select only feature columns for prediction
        feature_cols = ['macd_line', 'macd_signal', 'rsi', 'adx']
        # Simplified ensemble logic
        xgb_preds = self.xgb_model.predict_proba(features[feature_cols])
        # LSTM prediction logic would go here
        return xgb_preds[:, 1] # Probability of "Up"

    def generate_target_weights(self, df: pd.DataFrame) -> pd.DataFrame:
        # Generate signals and map to weights
        probabilities = self.predict_direction(df)
        # Handle empty/div-by-zero
        if probabilities.sum() == 0:
            weights = np.ones(len(probabilities)) / len(probabilities)
        else:
            weights = probabilities / probabilities.sum()
        
        # Ensure correct mapping
        features = self.prepare_features(df)
        return pd.DataFrame({'ticker': df.loc[features.index, 'symbol'], 'weight': weights})
