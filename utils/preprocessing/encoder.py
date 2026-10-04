"""
AgriSmartAI - Categorical Encoder Module
Provides scikit-learn based encoding for target labels and categorical soil features.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from typing import Tuple, Dict, Any

class CategoricalEncoder:
    def __init__(self):
        self.label_encoders = {}
        self.onehot_encoders = {}
        self.mappings = {}

    def encode_label(self, y: pd.Series, col_name: str = "target") -> Tuple[np.ndarray, Dict[str, int]]:
        """Encodes target string series to integer array using LabelEncoder."""
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        mapping = {str(label): int(idx) for idx, label in enumerate(le.classes_)}
        self.label_encoders[col_name] = le
        self.mappings[col_name] = mapping
        return y_encoded, mapping

    def encode_onehot(self, df: pd.DataFrame, cat_cols: list) -> pd.DataFrame:
        """One-hot encodes specified categorical columns in a DataFrame."""
        df_encoded = df.copy()
        for col in cat_cols:
            if col in df_encoded.columns:
                ohe = OneHotEncoder(sparse_output=False, drop='first', handle_unknown='ignore')
                encoded_array = ohe.fit_transform(df_encoded[[col]])
                feature_names = [f"{col}_{cat}" for cat in ohe.categories_[0][1:]]
                df_ohe = pd.DataFrame(encoded_array, columns=feature_names, index=df_encoded.index)
                
                df_encoded = pd.concat([df_encoded.drop(columns=[col]), df_ohe], axis=1)
                self.onehot_encoders[col] = ohe
                self.mappings[col] = list(ohe.categories_[0])
        return df_encoded
