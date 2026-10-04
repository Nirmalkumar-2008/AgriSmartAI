"""
AgriSmartAI Models Package
"""
from utils.models.crop_recommendation import CropRecommendationTrainer
from utils.models.yield_prediction import YieldPredictionTrainer
from utils.models.fertilizer_recommendation import FertilizerRecommendationTrainer
from utils.models.irrigation_recommendation import SmartIrrigationEngine

__all__ = [
    "CropRecommendationTrainer",
    "YieldPredictionTrainer",
    "FertilizerRecommendationTrainer",
    "SmartIrrigationEngine"
]
