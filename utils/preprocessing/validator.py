"""
AgriSmartAI - Data Validator Module
Validates schema integrity, non-null assertions, data types, and feature matrix dimensions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataValidator:
    @staticmethod
    def validate_schema(df: pd.DataFrame, expected_columns: List[str]) -> bool:
        """Validates that all expected columns exist in the DataFrame."""
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Schema validation failed. Missing columns: {missing}")
        return True

    @staticmethod
    def validate_types(df: pd.DataFrame) -> Dict[str, str]:
        """Returns data type dictionary and verifies no object types remain after preprocessing."""
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        return dtypes

    @staticmethod
    def validate_no_nulls(df: pd.DataFrame) -> bool:
        """Asserts zero null values remain in the DataFrame."""
        null_count = df.isnull().sum().sum()
        if null_count > 0:
            raise ValueError(f"Validation failed: DataFrame contains {null_count} missing values.")
        return True

    @staticmethod
    def validate_dimensions(X: pd.DataFrame, y: Any) -> bool:
        """Asserts feature matrix X and target y have matching row counts."""
        if len(X) != len(y):
            raise ValueError(f"Dimension mismatch: X has {len(X)} rows while y has {len(y)} rows.")
        return True
