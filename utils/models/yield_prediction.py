"""
AgriSmartAI - Crop Yield Prediction Model Trainer & Pipeline Manager
Manages 80:20 train/test split, regression model comparison (Linear Regression,
Decision Tree, Random Forest, XGBoost, LightGBM), hyperparameter tuning, and serialization.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from utils.evaluation.regression_metrics import RegressionEvaluator

class YieldPredictionTrainer:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {}
        self.best_model = None
        self.best_model_name = ""
        self.evaluation_results = {}

    def split_data(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Splits dataset into training and testing sets (80:20)."""
        return train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state
        )

    def train_baseline_models(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Initializes and trains 5 regression algorithms."""
        self.models["Linear Regression"] = LinearRegression()
        self.models["Decision Tree"] = DecisionTreeRegressor(random_state=self.random_state)
        self.models["Random Forest"] = RandomForestRegressor(n_estimators=100, random_state=self.random_state)
        self.models["XGBoost"] = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=self.random_state)
        self.models["LightGBM"] = LGBMRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=self.random_state, verbosity=-1)

        for name, model in self.models.items():
            model.fit(X_train, y_train)

        return self.models

    def evaluate_models(self, X_test: np.ndarray, y_test: np.ndarray) -> pd.DataFrame:
        """Evaluates all trained regression models on test set."""
        results = []
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            evaluator = RegressionEvaluator(y_test, y_pred)
            metrics = evaluator.get_metrics()
            metrics["Model"] = name
            results.append(metrics)
            self.evaluation_results[name] = {
                "metrics": metrics,
                "y_pred": y_pred,
                "evaluator": evaluator
            }

        df_results = pd.DataFrame(results)[["Model", "r2_score", "rmse", "mae", "mse", "mape"]]
        return df_results.sort_values(by="r2_score", ascending=False).reset_index(drop=True)

    def tune_best_model(self, X_train: np.ndarray, y_train: np.ndarray, model_name: str = "Random Forest") -> Any:
        """Performs hyperparameter tuning for chosen model family."""
        if model_name == "Random Forest":
            base_model = RandomForestRegressor(random_state=self.random_state)
            param_grid = {
                "n_estimators": [50, 100, 150],
                "max_depth": [None, 10, 20],
                "min_samples_split": [2, 5]
            }
        elif model_name == "XGBoost":
            base_model = XGBRegressor(random_state=self.random_state)
            param_grid = {
                "n_estimators": [50, 100, 150],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.05, 0.1, 0.2]
            }
        else:
            base_model = LGBMRegressor(random_state=self.random_state, verbosity=-1)
            param_grid = {
                "n_estimators": [50, 100, 150],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.05, 0.1, 0.2]
            }

        grid_search = GridSearchCV(base_model, param_grid, cv=5, scoring="r2", n_jobs=-1)
        grid_search.fit(X_train, y_train)

        self.best_model = grid_search.best_estimator_
        self.best_model_name = f"{model_name} (Tuned)"
        self.models[self.best_model_name] = self.best_model

        return grid_search.best_params_

    def save_model(self, output_path: str):
        """Serializes the best performing trained regression model artifact."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joblib.dump(self.best_model, output_path)
        print(f"Saved best regression model ({self.best_model_name}) to: {output_path}")
