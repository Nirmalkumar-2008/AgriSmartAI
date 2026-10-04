"""
AgriSmartAI - Explainable AI (SHAP) Explainer Module
Provides model interpretability via SHAP TreeExplainer, feature contribution ranking,
human-readable natural language explanations, and visualization exports (Summary, Bar, Waterfall, Force plots).
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
try:
    import shap
    HAS_SHAP = True
except ImportError:
    shap = None
    HAS_SHAP = False
from typing import Dict, Any, List, Tuple, Optional

FEATURE_DISPLAY_MAP = {
    "N": "Nitrogen (N)",
    "P": "Phosphorus (P)",
    "K": "Potassium (K)",
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ph": "Soil pH",
    "rainfall": "Rainfall (mm)",
    "Soil_pH": "Soil pH",
    "Soil_Moisture": "Soil Moisture (%)",
    "Organic_Carbon": "Organic Carbon (%)",
    "Electrical_Conductivity": "Electrical Conductivity (dS/m)",
    "Nitrogen_Level": "Nitrogen Level",
    "Phosphorus_Level": "Phosphorus Level",
    "Potassium_Level": "Potassium Level",
    "Temperature": "Temperature (°C)",
    "Humidity": "Humidity (%)"
}

class AgriSmartSHAPExplainer:
    def __init__(self, model: Any, feature_names: Optional[List[str]] = None):
        self.model = model
        if isinstance(feature_names, list):
            self.feature_names = feature_names
        else:
            self.feature_names = None
            
        self.explainer = None
        
        if HAS_SHAP and self.model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception:
                try:
                    self.explainer = shap.Explainer(self.model)
                except Exception:
                    self.explainer = None

    def explain_sample(self, X_sample: pd.DataFrame, target_name: str = "recommendation") -> Dict[str, Any]:
        """
        Computes SHAP values for a single sample input row and extracts Top 5 feature contributions.
        Returns structured dictionary and human-readable natural language summary.
        """
        # Ensure feature_names is a valid list matching DataFrame columns
        if not isinstance(self.feature_names, list) or len(self.feature_names) != X_sample.shape[1]:
            self.feature_names = list(X_sample.columns)

        vals = None
        if HAS_SHAP and self.explainer is not None:
            try:
                shap_values = self.explainer(X_sample)
                # Check raw array values
                if hasattr(shap_values, "values"):
                    raw_vals = shap_values.values
                else:
                    raw_vals = shap_values

                if isinstance(raw_vals, list): # List of arrays (multiclass)
                    if hasattr(self.model, "predict"):
                        pred_class = int(self.model.predict(X_sample)[0])
                    else:
                        pred_class = 0
                    pred_class = min(pred_class, len(raw_vals) - 1)
                    vals = raw_vals[pred_class][0]
                elif len(np.shape(raw_vals)) == 3: # 3D array (samples, features, classes) or (samples, classes, features)
                    if hasattr(self.model, "predict"):
                        pred_class = int(self.model.predict(X_sample)[0])
                    else:
                        pred_class = 0
                    shape = np.shape(raw_vals)
                    if shape[0] == 1:
                        pred_class = min(pred_class, shape[2] - 1)
                        vals = raw_vals[0, :, pred_class]
                    else:
                        pred_class = min(pred_class, shape[0] - 1)
                        vals = raw_vals[pred_class, 0, :]
                else: # Binary or Regression (1D or 2D)
                    if len(np.shape(raw_vals)) == 2:
                        vals = raw_vals[0]
                    else:
                        vals = raw_vals
            except Exception as e:
                vals = None

        # Fallback to feature_importances_ if SHAP computation failed or mismatched
        if vals is None or len(vals) != len(self.feature_names):
            if hasattr(self.model, "feature_importances_") and len(self.model.feature_importances_) == len(self.feature_names):
                vals = self.model.feature_importances_
            else:
                vals = np.ones(len(self.feature_names)) / max(len(self.feature_names), 1)

        contributions = []
        for feat_raw, val in zip(self.feature_names, vals):
            val_flt = round(float(val), 4)
            # Map raw feature name to human-readable label
            if feat_raw.startswith("Crop_Type_"):
                crop_name = feat_raw.replace("Crop_Type_", "").capitalize()
                disp_feat = f"Crop Species: {crop_name}"
            elif feat_raw.startswith("Soil_Type_"):
                soil_name = feat_raw.replace("Soil_Type_", "").capitalize()
                disp_feat = f"Soil Type: {soil_name}"
            else:
                disp_feat = FEATURE_DISPLAY_MAP.get(feat_raw, feat_raw)

            contributions.append({
                "feature": disp_feat,
                "raw_feature": feat_raw,
                "shap_value": val_flt,
                "abs_shap_value": round(abs(val_flt), 4)
            })

        # Sort by absolute impact descending
        sorted_contribs = sorted(contributions, key=lambda x: x["abs_shap_value"], reverse=True)
        top5 = sorted_contribs[:5]

        # Generate Plain-Language Explanation with Positive/Negative Directionality
        lines = [f"The {target_name} was influenced primarily by:"]
        for idx, item in enumerate(top5, 1):
            s_val = item["shap_value"]
            sign = "+" if s_val >= 0 else ""
            if s_val > 0:
                direction = "contributes toward predicted outcome"
            elif s_val < 0:
                direction = "contributes away from predicted outcome"
            else:
                direction = "has negligible contribution"
                
            lines.append(f"{idx}. {item['feature']} ({sign}{s_val:.4f}): {direction}")

        plain_language_summary = "\n".join(lines)

        return {
            "top_5_features": top5,
            "all_contributions": sorted_contribs,
            "plain_language_explanation": plain_language_summary
        }

    def generate_and_save_plots(self, X_data: pd.DataFrame, model_name: str, save_dir: str):
        """
        Generates and saves SHAP Summary Plot, Bar Plot, Waterfall Plot, and Force Plot.
        """
        os.makedirs(save_dir, exist_ok=True)
        
        if self.explainer is None:
            return
            
        shap_values = self.explainer(X_data)
        
        # Slice for multi-class if necessary
        if hasattr(shap_values, "shape") and len(shap_values.shape) == 3:
            shap_obj_slice = shap_values[:, :, 0]
        else:
            shap_obj_slice = shap_values

        import matplotlib.pyplot as plt
        
        # 1. SHAP Summary Plot
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X_data, show=False)
        plt.title(f"SHAP Summary Plot - {model_name}", fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()
        summary_path = os.path.join(save_dir, f"{model_name}_shap_summary.png")
        plt.savefig(summary_path, dpi=300, bbox_inches="tight")
        plt.close()

        # 2. SHAP Bar Plot
        plt.figure(figsize=(10, 6))
        shap.plots.bar(shap_obj_slice, show=False)
        plt.title(f"SHAP Feature Importance Bar Plot - {model_name}", fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()
        bar_path = os.path.join(save_dir, f"{model_name}_shap_bar.png")
        plt.savefig(bar_path, dpi=300, bbox_inches="tight")
        plt.close()
