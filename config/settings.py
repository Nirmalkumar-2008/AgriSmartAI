"""
AgriSmartAI Configuration Settings
Contains OpenWeatherMap API credentials, thresholds, and environment settings.
"""

import os

# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_openweather_api_key_here")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CITY = "Bengaluru,IN"

# Smart Irrigation Thresholds
IRRIGATION_THRESHOLDS = {
    "HIGH_TEMP_C": 32.0,
    "LOW_HUMIDITY_PCT": 40.0,
    "HIGH_HUMIDITY_PCT": 75.0,
    "RAINFALL_TRIGGER_MM": 1.0,
    "CRITICAL_SOIL_MOISTURE_LOW": 30.0,
    "CRITICAL_SOIL_MOISTURE_HIGH": 70.0,
    "HIGH_WIND_SPEED_MS": 8.0
}
