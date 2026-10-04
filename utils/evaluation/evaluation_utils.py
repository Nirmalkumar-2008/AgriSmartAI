"""
AgriSmartAI - Extended Evaluation Utilities Module
Provides cross-validation, multiclass classification metrics, regression metrics,
weather API evaluation, and figure generation routines for evaluation pipelines.
"""

import os
import json
import time
import requests
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
from sklearn.model_selection import StratifiedKFold, KFold, cross_val_score
from typing import Dict, Any, List, Tuple

class ModelEvaluatorUtils:
    @staticmethod
    def evaluate_classification_model(
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        labels: List[str] = None,
        cv: int = 5,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Trains classification model, evaluates on test set, and performs 5-fold Stratified Cross-Validation.
        """
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec_w = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec_w = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1_w = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        prec_m = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec_m = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_m = f1_score(y_test, y_pred, average="macro", zero_division=0)

        # 5-Fold Stratified Cross Validation
        skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
        cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="f1_weighted", n_jobs=-1)

        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))

        cm = confusion_matrix(y_test, y_pred)
        clf_rep = classification_report(y_test, y_pred, target_names=labels, zero_division=0, output_dict=True)

        return {
            "accuracy": float(acc),
            "precision_weighted": float(prec_w),
            "recall_weighted": float(rec_w),
            "f1_weighted": float(f1_w),
            "precision_macro": float(prec_m),
            "recall_macro": float(rec_m),
            "f1_macro": float(f1_m),
            "cv_mean": cv_mean,
            "cv_std": cv_std,
            "cv_formatted": f"{cv_mean*100:.2f}% ± {cv_std*100:.2f}%",
            "y_pred": y_pred,
            "confusion_matrix": cm,
            "classification_report_dict": clf_rep,
            "fitted_model": model
        }

    @staticmethod
    def evaluate_regression_model(
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        cv: int = 5,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Trains regression model, evaluates on test set, and performs 5-Fold Cross Validation.
        """
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        try:
            mape = float(mean_absolute_percentage_error(y_test, y_pred) * 100)
        except Exception:
            residuals = y_test - y_pred
            mape = float(np.mean(np.abs(residuals / (y_test + 1e-8))) * 100)

        # 5-Fold Cross Validation for R2
        kf = KFold(n_splits=cv, shuffle=True, random_state=random_state)
        cv_scores = cross_val_score(model, X_train, y_train, cv=kf, scoring="r2", n_jobs=-1)
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))

        return {
            "r2_score": r2,
            "rmse": rmse,
            "mae": mae,
            "mape": mape,
            "cv_r2_mean": cv_mean,
            "cv_r2_std": cv_std,
            "cv_formatted": f"{cv_mean:.4f} ± {cv_std:.4f}",
            "y_pred": y_pred,
            "residuals": y_test - y_pred,
            "fitted_model": model
        }
