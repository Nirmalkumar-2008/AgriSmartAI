"""
AgriSmartAI - Fertilizer Recommendation Evaluator Module
Provides metrics computation (Accuracy, Precision, Recall, F1-Score),
classification reports, and confusion matrix plotting routines.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from typing import Dict, Any, List

class FertilizerEvaluator:
    def __init__(self, y_true: np.ndarray, y_pred: np.ndarray, labels: List[str] = None):
        self.y_true = np.array(y_true)
        self.y_pred = np.array(y_pred)
        self.labels = labels

    def get_metrics(self) -> Dict[str, float]:
        """Calculates accuracy, weighted precision, recall, and F1-score."""
        return {
            "accuracy": float(accuracy_score(self.y_true, self.y_pred)),
            "precision": float(precision_score(self.y_true, self.y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(self.y_true, self.y_pred, average="weighted", zero_division=0)),
            "f1_score": float(f1_score(self.y_true, self.y_pred, average="weighted", zero_division=0))
        }

    def get_classification_report(self) -> str:
        """Generates detailed text classification report."""
        return classification_report(self.y_true, self.y_pred, target_names=self.labels, zero_division=0)

    def get_confusion_matrix(self) -> np.ndarray:
        """Computes confusion matrix."""
        return confusion_matrix(self.y_true, self.y_pred)

    def plot_confusion_matrix(self, title: str = "Fertilizer Confusion Matrix", save_path: str = None) -> plt.Figure:
        """Plots annotated confusion matrix heatmap."""
        cm = self.get_confusion_matrix()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Greens",
            xticklabels=self.labels if self.labels else "auto",
            yticklabels=self.labels if self.labels else "auto",
            ax=ax
        )
        ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
        ax.set_xlabel("Predicted Fertilizer Type", fontsize=12)
        ax.set_ylabel("True Fertilizer Type", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            
        return fig
