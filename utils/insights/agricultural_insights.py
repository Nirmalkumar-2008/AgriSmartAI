"""
AgriSmartAI - Agricultural Insights & Alerts Engine
Analyzes farmer inputs, live weather metrics, soil parameters, and ML predictions
to generate actionable, expert agronomist insights and color-coded alerts.
"""

from typing import Dict, Any, List

class AgriculturalInsightsEngine:
    def __init__(self):
        pass

    def _get_float(self, data_dict: Dict[str, Any], keys: List[str], default_val: float) -> float:
        """Safely extracts float value from dictionary checking multiple key aliases."""
        for k in keys:
            val = data_dict.get(k)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return default_val

    def generate_insights(
        self,
        farmer_input: Dict[str, Any],
        weather_data: Dict[str, Any],
        prediction_res: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generates an array of structured agricultural insights and alerts.
        Severity categories: 'warning' (red), 'caution' (yellow), 'success' (green), 'info' (blue).
        """
        insights = []

        # Weather API parsing first
        weather_temp = self._get_float(weather_data, ["temperature", "temp"], 28.5)
        weather_humidity = self._get_float(weather_data, ["humidity"], 55.0)
        weather_rainfall = self._get_float(weather_data, ["rainfall"], 0.0)
        wind_speed_ms = self._get_float(weather_data, ["wind_speed"], 3.2)
        wind_speed_kmh = wind_speed_ms * 3.6

        # Parse soil & farmer variables with fallbacks to weather data
        n = self._get_float(farmer_input, ["Nitrogen", "N"], 50.0)
        p = self._get_float(farmer_input, ["Phosphorus", "P"], 50.0)
        k = self._get_float(farmer_input, ["Potassium", "K"], 50.0)
        ph = self._get_float(farmer_input, ["pH", "ph"], 6.5)
        temp = self._get_float(farmer_input, ["Temperature", "temperature", "temp"], weather_temp)
        humidity = self._get_float(farmer_input, ["Humidity", "humidity"], weather_humidity)
        rainfall = self._get_float(farmer_input, ["Rainfall", "rainfall"], weather_rainfall)
        moisture = self._get_float(farmer_input, ["Soil_Moisture", "soil_moisture", "moisture"], 45.0)

        # Prediction results parsing
        raw_yield = prediction_res.get("predicted_yield_tons_per_ha")
        predicted_yield = float(raw_yield) if raw_yield is not None else None
        conf_scores = prediction_res.get("confidence_scores", {})
        crop_conf = float(conf_scores.get("crop_recommendation_confidence_pct", 95.0))

        # 1. Nutrient Rules
        if n < 40.0:
            insights.append({
                "severity": "warning",
                "title": "Low Nitrogen Level",
                "message": f"Nitrogen level ({n:.1f} mg/kg) is below the optimal threshold (40 mg/kg).",
                "recommendation": "Increase Nitrogen fertilizer application by approximately 20-30 kg/ha using Urea or NPK balanced fertilizer."
            })

        if p < 25.0:
            insights.append({
                "severity": "warning",
                "title": "Low Phosphorus Level",
                "message": f"Phosphorus level ({p:.1f} mg/kg) is deficient in soil.",
                "recommendation": "Apply phosphorus-rich fertilizer such as DAP (Di-Ammonium Phosphate) or Single Super Phosphate."
            })

        if k < 25.0:
            insights.append({
                "severity": "warning",
                "title": "Low Potassium Level",
                "message": f"Potassium level ({k:.1f} mg/kg) is below optimal crop requirements.",
                "recommendation": "Increase Potash fertilizer (MOP / Muriate of Potash) by 15-25 kg/ha."
            })

        # 2. Soil pH Rules
        if ph < 6.0:
            insights.append({
                "severity": "warning",
                "title": "Acidic Soil Condition",
                "message": f"Soil pH ({ph:.1f}) is acidic (< 6.0), which restricts phosphorus and calcium availability.",
                "recommendation": "Apply agricultural lime (calcium carbonate) or organic compost before sowing."
            })
        elif ph > 7.8:
            insights.append({
                "severity": "warning",
                "title": "Alkaline Soil Condition",
                "message": f"Soil pH ({ph:.1f}) is alkaline (> 7.8), which may cause micronutrient deficiencies.",
                "recommendation": "Apply agricultural gypsum or elemental sulfur-based amendments to lower soil pH."
            })

        # 3. Temperature Rules
        if temp > 35.0 or weather_temp > 35.0:
            insights.append({
                "severity": "warning",
                "title": "Heat Stress Warning",
                "message": f"Ambient temperature ({max(temp, weather_temp):.1f}°C) exceeds 35°C, causing heat stress.",
                "recommendation": "Schedule irrigation during early morning or late evening hours to minimize evapotranspiration losses."
            })
        elif temp < 15.0 or weather_temp < 15.0:
            insights.append({
                "severity": "warning",
                "title": "Cold Stress Warning",
                "message": f"Low ambient temperature ({min(temp, weather_temp):.1f}°C) may delay germination.",
                "recommendation": "Monitor crop growth closely and protect sensitive seedlings."
            })

        # 4. Humidity & Disease Rules
        if humidity > 85.0 or weather_humidity > 85.0:
            insights.append({
                "severity": "warning",
                "title": "High Fungal Disease Risk",
                "message": f"Relative atmospheric humidity ({max(humidity, weather_humidity):.1f}%) is very high.",
                "recommendation": "Monitor crop leaves for fungal blight or rust symptoms and consider applying preventative organic fungicides."
            })

        # 5. Rainfall & Irrigation Rules
        if rainfall > 10.0 or weather_rainfall > 10.0:
            insights.append({
                "severity": "info",
                "title": "Rainfall Expected / Active",
                "message": f"Recent or forecasted rainfall ({max(rainfall, weather_rainfall):.1f} mm) detected.",
                "recommendation": "Postpone artificial irrigation for 24 to 48 hours to conserve water."
            })

        # 6. Soil Moisture Rules
        if moisture < 30.0:
            insights.append({
                "severity": "warning",
                "title": "Severe Soil Drought",
                "message": f"Soil moisture ({moisture:.1f}%) is below 30%, indicating critical moisture deficit.",
                "recommendation": "Initiate immediate irrigation to prevent crop wilting."
            })
        elif moisture > 80.0:
            insights.append({
                "severity": "caution",
                "title": "Waterlogging & Oxygen Deficit Risk",
                "message": f"Soil moisture is extremely high ({moisture:.1f}%), risking root hypoxia.",
                "recommendation": "Ensure proper field drainage and halt irrigation until moisture drops below 70%."
            })

        # 7. Yield Rules (Only evaluated if predicted_yield is calculated)
        if predicted_yield is not None:
            if predicted_yield > 8.0:
                insights.append({
                    "severity": "success",
                    "title": "High Expected Yield",
                    "message": f"Predicted crop yield is excellent ({predicted_yield:.2f} tons/hectare).",
                    "recommendation": "Maintain current soil nutrient, pest control, and water management practices."
                })
            elif predicted_yield < 4.0:
                insights.append({
                    "severity": "warning",
                    "title": "Low Yield Forecast",
                    "message": f"Predicted crop yield is below average ({predicted_yield:.2f} tons/hectare).",
                    "recommendation": "Review soil fertility, irrigation scheduling, and crop suitability to improve productivity."
                })

        # 8. Confidence Rules
        if crop_conf > 95.0:
            insights.append({
                "severity": "success",
                "title": "High Confidence Prediction",
                "message": f"Crop recommendation confidence score is {crop_conf:.1f}%.",
                "recommendation": "The AI recommendation is highly reliable based on historical agronomic patterns."
            })
        elif crop_conf < 80.0:
            insights.append({
                "severity": "caution",
                "title": "Moderate Confidence Prediction",
                "message": f"Crop recommendation confidence score is {crop_conf:.1f}%.",
                "recommendation": "Consider conducting localized soil testing and field verification before planting."
            })

        # 9. Weather Risk Rules
        if wind_speed_kmh > 20.0:
            insights.append({
                "severity": "caution",
                "title": "Strong Winds Detected",
                "message": f"Wind speed ({wind_speed_kmh:.1f} km/h) is high.",
                "recommendation": "Avoid pesticide or foliar fertilizer spraying to prevent chemical drift and loss."
            })

        if weather_rainfall > 25.0 or rainfall > 25.0:
            insights.append({
                "severity": "warning",
                "title": "Heavy Precipitation Warning",
                "message": f"Heavy rain ({max(rainfall, weather_rainfall):.1f} mm) may cause nutrient leaching.",
                "recommendation": "Inspect field bunds, improve drainage channels, and split fertilizer applications."
            })

        return insights
