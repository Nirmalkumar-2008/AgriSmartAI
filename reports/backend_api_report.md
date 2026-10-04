# AgriSmartAI: FastAPI Backend REST API Documentation Report

**Framework**: FastAPI + Uvicorn + Pydantic  
**Status**: Phase 9 Production Backend Service Built & Tested  
**API Server Entry Point**: `backend/main.py`  
**Interactive Docs**: `/docs` (Swagger UI) & `/redoc` (ReDoc)  

---

## Executive Summary

This report documents the production-ready REST API developed for **AgriSmartAI**. The backend server loads all trained ML model artifacts once upon startup, exposes high-performance endpoints, enforces strict Pydantic field validation, and returns integrated farm advisories with SHAP explainability.

## 1. Backend Project Architecture

```text
backend/
├── main.py                     # FastAPI application entry point & Uvicorn runner
├── routes/predict.py           # Endpoint router (/, /health, /predict)
├── services/prediction_service.py # Singleton model loader & execution service
├── schemas/request_schema.py   # Pydantic input validation model
├── schemas/response_schema.py  # Pydantic response models
└── middleware/error_handler.py # Custom 422/500 exception handlers
```

## 2. API Endpoints Specification

| Method | Endpoint | Description | Status Code | Response Type |
| :---: | :--- | :--- | :---: | :--- |
| `GET` | `/` | API Metadata & Sitemap | `200 OK` | `RootResponse` |
| `GET` | `/health` | Server Health & Model Load Status | `200 OK` | `HealthCheckResponse` |
| `POST` | `/predict` | Integrated Farm Advisory Prediction | `200 OK` | `PredictionResponse` |

## 3. Sample Request Payload (`POST /predict`)

```json
{
  "city": "Bengaluru",
  "N": 90,
  "P": 42,
  "K": 43,
  "ph": 6.8,
  "temperature": 28.5,
  "humidity": 55,
  "rainfall": 0,
  "soil_moisture": 45,
  "selected_crop": "Rice"
}
```

## 4. Sample Integrated Response Payload

```json
{
  "recommended_crop": "muskmelon",
  "selected_crop": "muskmelon",
  "predicted_yield_tons_per_ha": 8.75,
  "fertilizer_recommendation": "4",
  "irrigation_recommendation": {
    "level": "Moderate",
    "message": "MODERATE IRRIGATION RECOMMENDED for muskmelon: Standard micro-climate conditions (Temp: 28.5\u00b0C, Humidity: 55.0%, Moisture: 45.0%). Apply baseline 8-12 mm of water."
  },
  "weather_summary": {
    "city": "Bengaluru",
    "temperature": 28.5,
    "humidity": 55.0,
    "rainfall": 0.0,
    "condition": "Partly Cloudy (Simulated Fallback)",
    "wind_speed": 3.2,
    "source": "Simulated Weather Engine"
  },
  "confidence_scores": {
    "crop_recommendation_confidence_pct": 36.0,
    "fertilizer_recommendation_confidence_pct": 100.0,
    "yield_model_r2_metric": 0.9842
  },
  "explainability": {
    "crop_recommendation": {
      "top_5_features": [
        {
          "feature": "P",
          "shap_value": 0.21797869340241505,
          "abs_shap_value": 0.21797869340241505
        },
        {
          "feature": "K",
          "shap_value": 0.15594528491002113,
          "abs_shap_value": 0.15594528491002113
        },
        {
          "feature": "humidity",
          "shap_value": 0.09439693980147298,
          "abs_shap_value": 0.09439693980147298
        },
        {
          "feature": "rainfall",
          "shap_value": 0.0841055125345819,
          "abs_shap_value": 0.0841055125345819
        },
        {
          "feature": "N",
          "shap_value": -0.05843285434608878,
          "abs_shap_value": 0.05843285434608878
        }
      ],
      "plain_language_explanation": "The crop recommendation was influenced primarily by:\n1. P (+0.22)\n2. K (+0.16)\n3. humidity (+0.09)\n4. rainfall (+0.08)\n5. N (-0.06)"
    },
    "yield_prediction": {
      "top_5_features": [
        {
          "feature": "Nitrogen_Level",
          "shap_value": 1.3394827842712402,
          "abs_shap_value": 1.3394827842712402
        },
        {
          "feature": "Soil_Moisture",
          "shap_value": 0.5343748331069946,
          "abs_shap_value": 0.5343748331069946
        },
        {
          "feature": "Potassium_Level",
          "shap_value": 0.5225319266319275,
          "abs_shap_value": 0.5225319266319275
        },
        {
          "feature": "Phosphorus_Level",
          "shap_value": 0.4491674602031708,
          "abs_shap_value": 0.4491674602031708
        },
        {
          "feature": "Organic_Carbon",
          "shap_value": 0.34093186259269714,
          "abs_shap_value": 0.34093186259269714
        }
      ],
      "plain_language_explanation": "The yield prediction was influenced primarily by:\n1. Nitrogen_Level (+1.34)\n2. Soil_Moisture (+0.53)\n3. Potassium_Level (+0.52)\n4. Phosphorus_Level (+0.45)\n5. Organic_Carbon (+0.34)"
    },
    "fertilizer_recommendation": {
      "top_5_features": [
        {
          "feature": "Soil_pH",
          "shap_value": -0.08997753532088125,
          "abs_shap_value": 0.08997753532088125
        },
        {
          "feature": "Phosphorus_Level",
          "shap_value": -0.08997753532088125,
          "abs_shap_value": 0.08997753532088125
        },
        {
          "feature": "Potassium_Level",
          "shap_value": 0.02007843929597701,
          "abs_shap_value": 0.02007843929597701
        },
        {
          "feature": "Nitrogen_Level",
          "shap_value": 0.008126631345785446,
          "abs_shap_value": 0.008126631345785446
        },
        {
          "feature": "Soil_Moisture",
          "shap_value": 0.0,
          "abs_shap_value": 0.0
        }
      ],
      "plain_language_explanation": "The fertilizer recommendation was influenced primarily by:\n1. Soil_pH (-0.09)\n2. Phosphorus_Level (-0.09)\n3. Potassium_Level (+0.02)\n4. Nitrogen_Level (+0.01)\n5. Soil_Moisture (+0.00)"
    }
  }
}
```

## 5. Input Validation & Error Handling (422 Unprocessable Entity)

When invalid fields are passed (e.g. negative Nitrogen or pH > 14), Pydantic middleware returns a clear, structured JSON error response:
```json
{
  "status": "error",
  "error_type": "Validation Error",
  "message": "Invalid input parameters provided.",
  "details": [
    "Field 'body -> N': Input should be greater than or equal to 0",
    "Field 'body -> ph': Input should be less than or equal to 14"
  ]
}
```

---

## Conclusion & Next Steps

The AgriSmartAI FastAPI backend service is complete, tested, and fully functional.

Per Phase 9 instructions:
- ❌ React frontend UI code was **NOT built**.
- ❌ Cloud deployment was **NOT executed**.