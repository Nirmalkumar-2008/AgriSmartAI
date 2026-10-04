"""
AgriSmartAI - Data Cleaner Module
Handles missing value inspection/imputation, duplicate row removal, and IQR outlier detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any

class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_shape = df.shape
        self.outlier_report = {}

    def inspect_missing(self) -> Dict[str, int]:
        """Returns missing value count per column."""
        return self.df.isnull().sum().to_dict()

    def remove_duplicates(self) -> Tuple[pd.DataFrame, int]:
        """Removes duplicate rows and returns cleaned DataFrame along with count of dropped rows."""
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        dropped_count = initial_count - len(self.df)
        return self.df, dropped_count

    def detect_outliers_iqr(self, num_cols: list = None, factor: float = 1.5) -> Dict[str, Dict[str, Any]]:
        """
        Detects outliers using Interquartile Range (IQR) method.
        Does not drop rows automatically to preserve legitimate agronomic extremes.
        """
        if num_cols is None:
            num_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()

        report = {}
        for col in num_cols:
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (factor * iqr)
            upper_bound = q3 + (factor * iqr)
            
            outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            outlier_count = len(outliers)
            
            report[col] = {
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": int(outlier_count),
                "outlier_percentage": float(round((outlier_count / len(self.df)) * 100, 2))
            }
        
        self.outlier_report = report
        return report

    def get_cleaned_data(self) -> pd.DataFrame:
        return self.df
