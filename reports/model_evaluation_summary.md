# AgriSmartAI — Model Evaluation Summary Report

### Standard Evaluation vs. Robustness Evaluation Summary

This document synthesizes standard evaluation metrics and offline robustness testing across all four machine learning modules in AgriSmartAI.

---

## 1. Module Performance Overview

### 📍 Crop Recommendation Module
- **Production Model**: Random Forest Classifier
- **Standard Test Accuracy**: **99.55%**
- **5-Fold Cross Validation**: **99.55% ± 0.32%**
- **Balanced Accuracy**: **0.9955** | **Cohen's Kappa**: **0.9952**
- **Audit Verdict**: Verified genuine generalization backed by non-overlapping crop physiological growth niches.

### 🌾 Crop Yield Prediction Module
- **Production Model**: CatBoost Regressor
- **Standard Test $R^2$**: **0.988703**
- **Test RMSE**: **0.180528 tons/ha** | **MAE**: **0.144675 tons/ha** | **MAPE**: **1.61%**
- **5-Fold Cross Validation**: **0.987302 ± 0.000631**
- **Audit Verdict**: High precision continuous yield forecasting with zero target leakage.

### 🧪 Fertilizer Recommendation Module
- **Production Model**: Decision Tree Classifier (`max_depth=7`, 13 leaves)
- **Standard Test Accuracy**: **100.00%**
- **5-Fold Cross Validation**: **99.9875% ± 0.0250%**
- **Target Construction**: Deterministic rule-based mapping function (`map_fertilizer`).
- **Robustness Mean Accuracy (5% noise)**: **95.63% ± 0.25%**
- **Audit Verdict**: Flawless rule recovery with high resistance to input measurement noise.

### 💧 Smart Irrigation Module
- **Engine Type**: Real-time Weather API + Dynamic Agronomic Rule Engine
- **Status**: Live integration with OpenWeatherMap API.

---

## 2. Key Takeaways
1. Standard test performance and offline robustness testing are maintained as two separate evaluation categories.
2. Production model artifacts (`.pkl`) remain untouched.
