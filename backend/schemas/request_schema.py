"""
AgriSmartAI - Request Schemas
Pydantic model for farmer input validation with auto-weather retrieval and optional selected_crop for yield prediction.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

SUPPORTED_CROPS = [
    "rice", "maize", "chickpea", "kidneybeans", "pigeonpeas", "mothbeans",
    "mungbean", "blackgram", "lentil", "pomegranate", "banana", "mango",
    "grapes", "watermelon", "muskmelon", "apple", "orange", "papaya",
    "coconut", "cotton", "jute", "coffee", "wheat"
]

class PredictionRequest(BaseModel):
    city: str = Field(default="Bengaluru", description="City or region name for live weather lookup")
    N: float = Field(..., ge=0, le=250, description="Nitrogen level in soil (mg/kg)")
    P: float = Field(..., ge=0, le=250, description="Phosphorus level in soil (mg/kg)")
    K: float = Field(..., ge=0, le=250, description="Potassium level in soil (mg/kg)")
    ph: float = Field(..., ge=0, le=14, description="Soil pH value (0.0 to 14.0)")
    temperature: Optional[float] = Field(default=None, ge=-10, le=60, description="Optional pre-fetched ambient temperature in °C")
    humidity: Optional[float] = Field(default=None, ge=0, le=100, description="Optional pre-fetched relative humidity (%)")
    rainfall: Optional[float] = Field(default=None, ge=0, le=1000, description="Optional pre-fetched rainfall depth (mm)")
    soil_moisture: float = Field(..., ge=0, le=100, description="Manual soil moisture percentage (%)")
    selected_crop: Optional[str] = Field(default=None, description="Optional user-selected crop for yield, fertilizer, and irrigation predictions")

    @field_validator("selected_crop")
    @classmethod
    def validate_crop_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        clean_v = str(v).strip()
        if clean_v.lower() not in [c.lower() for c in SUPPORTED_CROPS]:
            raise ValueError(f"Invalid crop '{clean_v}'. Supported crops are: {', '.join(SUPPORTED_CROPS)}")
        return clean_v

    model_config = {
        "json_schema_extra": {
            "example": {
                "city": "Chennai",
                "N": 90,
                "P": 42,
                "K": 43,
                "ph": 6.5,
                "soil_moisture": 60,
                "selected_crop": "Rice"
            }
        }
    }
