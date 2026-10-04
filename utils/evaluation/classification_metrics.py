"""
AgriSmartAI - Classification Evaluator Module
Provides metrics computation, evaluation tables, and confusion matrix plotting routines.
"""

import pandas as pd
import numpy as np
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

class ClassificationEvaluator:
    def __init__(self, y_true: np.ndarray, y_pred: np.ndarray, labels: List[str] = None):
        self.y_true = y_true
        self.y_pred = y_pred
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

    def plot_confusion_matrix(self, title: str = "Confusion Matrix", save_path: str = None) -> plt.Figure:
        """Plots annotated confusion matrix heatmap."""
        cm = self.get_confusion_matrix()
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.labels if self.labels else "auto",
            yticklabels=self.labels if self.labels else "auto",
            ax=ax
        )
        ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
        ax.set_xlabel("Predicted Label", fontsize=12)
        ax.set_ylabel("True Label", fontsize=12)
        plt.xticks(rotation=90)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            
        return fig
