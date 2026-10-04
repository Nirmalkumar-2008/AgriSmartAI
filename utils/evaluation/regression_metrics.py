"""
AgriSmartAI - Regression Evaluator Module
Provides metrics computation (MAE, MSE, RMSE, R2 Score, MAPE), evaluation summaries,
and diagnostic plotting routines (Actual vs Predicted, Residual Analysis).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
from typing import Dict, Any, Tuple

class RegressionEvaluator:
    def __init__(self, y_true: np.ndarray, y_pred: np.ndarray):
        self.y_true = np.array(y_true)
        self.y_pred = np.array(y_pred)
        self.residuals = self.y_true - self.y_pred

    def get_metrics(self) -> Dict[str, float]:
        """Calculates MAE, MSE, RMSE, R2 Score, and MAPE."""
        mae = float(mean_absolute_error(self.y_true, self.y_pred))
        mse = float(mean_squared_error(self.y_true, self.y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(self.y_true, self.y_pred))
        try:
            mape = float(mean_absolute_percentage_error(self.y_true, self.y_pred) * 100)
        except Exception:
            mape = float(np.mean(np.abs(self.residuals / (self.y_true + 1e-8))) * 100)

        return {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2_score": r2,
            "mape": mape
        }

    def plot_actual_vs_predicted(self, model_name: str = "Regression Model", save_path: str = None) -> plt.Figure:
        """Plots Actual vs. Predicted values scatter chart with identity line."""
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.scatter(self.y_true, self.y_pred, alpha=0.5, color="#1f77b4", edgecolors="k", linewidth=0.5)
        
        min_val = min(min(self.y_true), min(self.y_pred))
        max_val = max(max(self.y_true), max(self.y_pred))
        ax.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect Prediction (45° Line)")
        
        ax.set_title(f"Actual vs. Predicted Yield ({model_name})", fontsize=16, fontweight="bold", pad=15)
        ax.set_xlabel("Actual Yield (tons/ha)", fontsize=13)
        ax.set_ylabel("Predicted Yield (tons/ha)", fontsize=13)
        ax.legend()
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            
        return fig

    def plot_residuals(self, model_name: str = "Regression Model", save_path: str = None) -> plt.Figure:
        """Plots Residuals vs Predicted values to inspect heteroscedasticity."""
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.scatter(self.y_pred, self.residuals, alpha=0.5, color="#2ca02c", edgecolors="k", linewidth=0.5)
        ax.axhline(0, color="red", linestyle="--", linewidth=2)
        
        ax.set_title(f"Residual Plot ({model_name})", fontsize=16, fontweight="bold", pad=15)
        ax.set_xlabel("Predicted Yield (tons/ha)", fontsize=13)
        ax.set_ylabel("Residuals (Actual - Predicted)", fontsize=13)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            
        return fig
