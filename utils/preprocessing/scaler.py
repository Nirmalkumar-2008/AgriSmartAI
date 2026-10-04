"""
AgriSmartAI - Feature Scaler Module
Provides scaling transformations (StandardScaler, RobustScaler, MinMaxScaler) for numerical features.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from typing import Tuple, Dict, Any

class FeatureScaler:
    def __init__(self, method: str = "standard"):
        self.method = method.lower()
        if self.method == "robust":
            self.scaler = RobustScaler()
        elif self.method == "minmax":
            self.scaler = MinMaxScaler()
        else:
            self.scaler = StandardScaler()

    def fit_transform(self, X: pd.DataFrame, num_cols: list = None) -> pd.DataFrame:
        """Fits scaler and transforms numerical features of DataFrame."""
        X_scaled = X.copy()
        if num_cols is None:
            num_cols = X_scaled.select_dtypes(include=[np.number]).columns.tolist()

        if num_cols:
            scaled_array = self.scaler.fit_transform(X_scaled[num_cols])
            scaled_df = pd.DataFrame(scaled_array, columns=num_cols, index=X_scaled.index)
            for c in num_cols:
                X_scaled[c] = scaled_df[c]
                
        return X_scaled

    def transform(self, X: pd.DataFrame, num_cols: list = None) -> pd.DataFrame:
        """Transforms numerical features using fitted scaler."""
        X_scaled = X.copy()
        if num_cols is None:
            num_cols = X_scaled.select_dtypes(include=[np.number]).columns.tolist()

        if num_cols:
            scaled_array = self.scaler.transform(X_scaled[num_cols])
            scaled_df = pd.DataFrame(scaled_array, columns=num_cols, index=X_scaled.index)
            for c in num_cols:
                X_scaled[c] = scaled_df[c]
                
        return X_scaled
