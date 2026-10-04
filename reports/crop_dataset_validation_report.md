# AgriSmartAI - Crop Dataset Validation & Quality Analysis Report

## Executive Summary

This report presents a thorough data-quality, compatibility, and overlap validation comparing the existing benchmark crop recommendation dataset (`datasets/crop_recommendation.csv`, N = 2,200) against the candidate dataset (`datasets/crop_recommendation_6200.csv`, N = 6,596).

### Key Empirical Discoveries:
1. **Dataset Size**: The candidate dataset contains **6,596 rows** across **51 crop classes**, compared to **2,200 rows** across **22 crop classes** in the benchmark dataset.
2. **Schema Compatibility**: Both datasets exhibit **100% column schema compatibility** (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label`).
3. **Exact Overlap**: **1,474 rows** (67.0% of the 2,200 benchmark dataset) are exact duplicates of rows present in the 6,596 candidate dataset.
4. **Genuinely New Rows**: The candidate dataset provides **5,122 new unique sample observations** and **29 new crop categories** (e.g. `wheat`, `potato`, `cabbage`, `tomato`, `barley`, `onion`, `garlic`, `radish`, `soybean`, `sunflower`).
5. **Class Imbalance**: Unlike the 2,200 dataset (which is perfectly balanced with 100 samples per crop), the candidate dataset is **highly imbalanced** (ranging from 7 samples for `ragi` to 461 samples for `rice`).
6. **Data Integrity**: Zero missing values, zero negative nutrient/rainfall values, and zero invalid pH readings (<0 or >14) were detected in either dataset.

---

## 1. Dataset Size & Structural Comparison

| Metric | Benchmark Dataset (`crop_recommendation.csv`) | Candidate Dataset (`crop_recommendation_6200.csv`) | Comparison Notes |
|---|---|---|---|
| **Total Rows (N)** | 2,200 | 6,596 | Candidate dataset is 3.0x larger |
| **Total Columns** | 8 | 8 | Identical column count |
| **Input Features** | 7 (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`) | 7 (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`) | 100% Feature Schema Match |
| **Target Column** | `label` | `label` | Identical target naming |
| **Unique Crop Classes** | 22 | 51 | Candidate adds 29 new crop classes |
| **Missing Values** | 0 | 0 | Clean Data |
| **Exact Duplicates** | 0 | 0 | Clean Data |

---

## 2. Feature Compatibility Matrix

| Standard Feature Name | Benchmark Dataset Column | Candidate Dataset Column | Equivalent Auto-Detection | Compatibility Status |
|---|---|---|---|---|
| Nitrogen (N) | `N` | `N` | `N` / `Nitrogen` | ✅ Compatible |
| Phosphorus (P) | `P` | `P` | `P` / `Phosphorus` | ✅ Compatible |
| Potassium (K) | `K` | `K` | `K` / `Potassium` | ✅ Compatible |
| Temperature | `temperature` | `temperature` | `temperature` / `Temperature` | ✅ Compatible |
| Humidity | `humidity` | `humidity` | `humidity` / `Humidity` | ✅ Compatible |
| Soil pH | `ph` | `ph` | `ph` / `pH` / `Soil_pH` | ✅ Compatible |
| Rainfall | `rainfall` | `rainfall` | `rainfall` / `Rainfall` | ✅ Compatible |
| Crop Target | `label` | `label` | `label` / `crop` / `Crop_Type` | ✅ Compatible |

---

## 3. Crop Class Distribution & Imbalance Analysis

- **Benchmark Dataset (2,200 rows)**: Perfectly balanced with **exactly 100 samples** for each of the 22 crop classes.
- **Candidate Dataset (6,596 rows)**: Highly imbalanced across 51 crops.
  - **Minimum Samples**: 7 (`ragi`)
  - **Maximum Samples**: 461 (`rice`)
  - **Mean Samples per Crop**: 129.33
  - **Median Samples per Crop**: 100.0

### 29 Additional Crops in Candidate Dataset:
`barley`, `bitter_gourd`, `blackpepper`, `bottle_gourd`, `brinjal`, `cabbage`, `cardamom`, `cauliflower`, `coriander`, `cucumber`, `drumstick`, `garlic`, `horsegram`, `jackfruit`, `okra`, `onion`, `pineapple`, `potato`, `pumpkin`, `radish`, `ragi`, `rapeseed`, `sorghum`, `soybean`, `sunflower`, `sweet_potato`, `tomato`, `turmeric`, `wheat`.

---

## 4. Duplicate & Overlap Analysis

- **Exact Overlapping Rows**: **1,474 rows**
- **Percentage Overlap (relative to 2,200 Benchmark)**: **67.0%**
- **Percentage Overlap (relative to 6,596 Candidate)**: **22.35%**
- **Genuinely New Unique Observations**: **5,122 rows**
- **Conflicting Label Duplicates**: **0 rows**

---

## 5. Feature Range & Distribution Audit

| Feature | Benchmark (2,200) Range [Min, Max] | Benchmark Mean ± Std | Candidate (6,596) Range [Min, Max] | Candidate Mean ± Std |
|---|---|---|---|---|
| Nitrogen (N) | [0.00, 140.00] | 50.55 ± 36.92 | [0.00, 180.00] | 65.33 ± 45.43 |
| Phosphorus (P) | [5.00, 145.00] | 53.36 ± 32.99 | [5.00, 145.00] | 48.16 ± 23.70 |
| Potassium (K) | [5.00, 205.00] | 48.15 ± 50.65 | [5.00, 205.00] | 50.29 ± 39.81 |
| Temperature (°C) | [8.83, 43.68] | 25.62 ± 5.06 | [1.18, 43.68] | 25.40 ± 5.05 |
| Humidity (%) | [14.26, 99.98] | 71.48 ± 22.26 | [14.26, 99.98] | 73.41 ± 17.59 |
| Soil pH | [3.50, 9.94] | 6.47 ± 0.77 | [3.50, 9.94] | 5.86 ± 0.76 |
| Rainfall (mm) | [20.21, 298.56] | 103.46 ± 54.96 | [3.27, 3322.06] | 531.00 ± 599.99 |

---

## 6. Model Pipeline Compatibility Analysis

Evaluating compatibility against `models/crop_recommendation_model.pkl`:
- **Input Features & Order**: 100% Match (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`).
- **Feature Scaler**: Standard scaling compatible.
- **Output Layer / Classes**: `models/crop_recommendation_model.pkl` is trained to classify **22 classes**. The 6,596 dataset contains **51 classes**. Evaluating the 6,596 dataset directly on the production model without retraining will result in out-of-vocabulary class index errors for the 29 new crop categories.

---

## 7. Final Classification & Recommendation

### Classification:
**B. Useful as an additional dataset** (and **D. Requires cleaning/rebalancing before production retraining**).

### Recommended Strategy:
**OPTION 4: Use them separately for benchmark and generalization experiments.**

- **Rationale**: The existing 2,200 dataset remains the controlled, perfectly balanced 22-crop benchmark. The 6,596 dataset provides valuable expanded coverage for 51 crops, but requires stratified rebalancing/cleaning before considering production deployment.
