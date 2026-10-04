# AgriSmartAI Architecture & Technical Specification

## Project Scope
AgriSmartAI delivers an enterprise-grade AI engine for precision agriculture. The architecture connects modular data pipelines, multi-model Machine Learning algorithms, explainability engines, and scalable deployment interfaces.

## Datasets Overview
1. **`crop_recommendation.csv`**: 2,200 samples with 7 numerical features (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`) and 1 multi-class label (`label`).
2. **`crop_yield.csv`**: 10,000 samples with soil and environmental features (`Soil_Type`, `Soil_pH`, `Soil_Moisture`, `Organic_Carbon`, `Electrical_Conductivity`, `Nitrogen_Level`, `Phosphorus_Level`, `Potassium_Level`, `Temperature`, `Humidity`).
3. **`fertilizer_recommendation.csv`**: 10,000 samples describing soil nutrient distributions and environmental characteristics.

## Pipeline Lifecycle
- **Stage 1: Dataset Analysis & EDA**: Exploratory analysis, schema validation, distributions, correlation analysis.
- **Stage 2: Preprocessing & Feature Engineering**: Imputation, scaling, categorical encoding, synthetic features (N-P-K ratios, moisture-pH interaction).
- **Stage 3: Model Architecture**: Evaluation of Random Forest, XGBoost, LightGBM, Gradient Boosting, SVM, and Multi-Layer Perceptrons.
- **Stage 4: Explainable AI (SHAP)**: Feature importance ranking, SHAP summary plots, dependence plots.
- **Stage 5: Serving & Deployment**: API endpoints (FastAPI/REST) and Interactive Web Dashboard.
