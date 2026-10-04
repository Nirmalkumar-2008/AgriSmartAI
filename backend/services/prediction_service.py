"""
AgriSmartAI - Prediction Service Module
Loads ML models once during startup and executes fusion recommendations.
"""

import os
from typing import Dict, Any
from utils.fusion.recommendation_engine import AgriSmartFusionEngine

class PredictionService:
    _instance = None
    _fusion_engine = None

    @classmethod
    def initialize_models(cls):
        """Loads all ML models, scalers, and encoders once during application startup."""
        if cls._fusion_engine is None:
            print("Loading AgriSmartAI ML Models & Artifacts...")
            cls._fusion_engine = AgriSmartFusionEngine()
            print("All models successfully loaded into memory.")

    @classmethod
    def is_healthy(cls) -> bool:
        """Returns True if models are initialized."""
        return cls._fusion_engine is not None

    @classmethod
    def predict(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes full multi-module recommendation fusion."""
        if cls._fusion_engine is None:
            cls.initialize_models()
        return cls._fusion_engine.generate_advisory(request_data)
