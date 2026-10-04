"""
AgriSmartAI - Response Schemas
Pydantic models for API responses supporting Top 3 AI Crop Recommendations,
independent user crop selection for Yield Prediction, Fertilizer Strategy, Smart Irrigation,
Agricultural Insights, SHAP Explainability, and Model Robustness Evaluation.
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    pressure: Optional[float] = 1013.0
    clouds: Optional[int] = 0
    condition: str
    source: Optional[str] = "OpenWeatherMap Live API"

class WeatherSummary(BaseModel):
    city: str
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    pressure: Optional[float] = 1013.0
    clouds: Optional[int] = 0
    condition: str
    source: str

class RecommendedCropItem(BaseModel):
    rank: int
    crop: str
    confidence_pct: float

class CropRecommendationItem(BaseModel):
    rank: int
    crop: str
    confidence: float

class IrrigationRecommendation(BaseModel):
    level: str
    water_depth_mm: str
    message: str

class ConfidenceScores(BaseModel):
    crop_recommendation_confidence_pct: float
    fertilizer_recommendation_confidence_pct: Optional[float] = 0.0
    yield_model_r2_metric: Optional[float] = 0.8989

class FeatureContribution(BaseModel):
    feature: str
    shap_value: float
    abs_shap_value: float

class ModuleExplanation(BaseModel):
    top_5_features: List[FeatureContribution]
    plain_language_explanation: str

class ExplainabilityPayload(BaseModel):
    crop_recommendation: Optional[ModuleExplanation] = None
    yield_prediction: Optional[ModuleExplanation] = None
    fertilizer_recommendation: Optional[ModuleExplanation] = None

class AgriculturalInsight(BaseModel):
    severity: str # 'warning', 'caution', 'success', 'info'
    title: str
    message: str
    recommendation: str

class PredictionResponse(BaseModel):
    recommended_crops: List[RecommendedCropItem]
    selected_crop: Optional[str] = None
    predicted_yield_tons_per_ha: Optional[float] = None
    fertilizer_recommendation: Optional[str] = None
    irrigation_recommendation: Optional[IrrigationRecommendation] = None
    agricultural_insights: List[AgriculturalInsight]
    explainability: Optional[ExplainabilityPayload] = None
    
    # Backward compatibility fields
    crop_source: Optional[str] = "automatic"
    recommended_crop: Optional[str] = None
    recommended_crop_confidence: Optional[float] = 0.0
    top_3_recommendations: Optional[List[CropRecommendationItem]] = None
    prediction_crop: Optional[str] = None
    weather_summary: Optional[WeatherSummary] = None
    confidence_scores: Optional[ConfidenceScores] = None

class HealthCheckResponse(BaseModel):
    status: str
    models_loaded: bool

class RootResponse(BaseModel):
    name: str
    version: str
    docs_url: str
    redoc_url: str
    health_url: str
    predict_url: str
    weather_url: str
    evaluation_url: Optional[str] = "/evaluation/fertilizer"

# Robustness Evaluation Schemas
class FertilizerStandardMetrics(BaseModel):
    model: str = "Decision Tree"
    accuracy: float = 1.00
    f1: float = 1.00
    cv_mean: float = 0.999875
    cv_std: float = 0.00025
    explanation: Optional[str] = None

class FertilizerRobustnessMetrics(BaseModel):
    model: str = "Decision Tree"
    mean_accuracy: float
    std_accuracy: float
    min_accuracy: float
    max_accuracy: float
    mean_f1: Optional[float] = None
    uncertainty_level: Optional[str] = None

class FertilizerSensitivityItem(BaseModel):
    Feature: str
    Perturbation: str
    Prediction_Change_Rate: float

class FertilizerModelCompItem(BaseModel):
    Model: str
    Standard_Accuracy: float
    Robust_Mean_Accuracy: float
    Robust_STD: float

class GeneralizationStatus(BaseModel):
    status: str = "GOOD"
    message: Optional[str] = None

class TargetConstructionInfo(BaseModel):
    type: str = "DETERMINISTIC_RULE_BASED"
    description: Optional[str] = None

class FertilizerEvaluationResponse(BaseModel):
    standard_evaluation: FertilizerStandardMetrics
    robustness_evaluation: FertilizerRobustnessMetrics
    feature_sensitivity: List[FertilizerSensitivityItem]
    model_comparison: List[Dict[str, Any]]
    generalization: GeneralizationStatus
    target_construction: TargetConstructionInfo
