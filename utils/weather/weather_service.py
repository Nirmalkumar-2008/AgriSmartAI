"""
AgriSmartAI - Weather Service
Integrates OpenWeatherMap REST API to fetch real-time atmospheric metrics.
Reads OPENWEATHER_API_KEY from .env using python-dotenv.
"""

import os
import logging
import requests
from dotenv import load_dotenv

try:
    from fastapi import HTTPException, status
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int = 500, detail: str = ""):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
        HTTP_500_INTERNAL_SERVER_ERROR = 500

from typing import Dict, Any

# Load environment variables from .env file prior to service initialization
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(project_root, ".env"))

logger = logging.getLogger("AgriSmartAI.WeatherService")

# Safe startup diagnostic (never exposes the key itself)
_api_key_check = os.getenv("OPENWEATHER_API_KEY", "").strip()
_is_key_configured = bool(_api_key_check)
print(f"OPENWEATHER_API_KEY configured: {_is_key_configured}")
logger.info(f"OPENWEATHER_API_KEY configured: {_is_key_configured}")

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str = None):
        if api_key:
            self.api_key = api_key.strip()
        else:
            self.api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()

    def get_weather(self, city: str) -> Dict[str, Any]:
        return self.fetch_current_weather(city)

    def fetch_current_weather(self, city: str) -> Dict[str, Any]:
        """
        Fetches live weather metrics for a specified city from OpenWeatherMap REST API.
        Returns temperature (°C), humidity (%), rainfall (mm), wind speed (m/s), pressure (hPa), cloud cover (%), condition, and source.
        """
        if not city or not city.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="City name must be provided."
            )

        city_name = city.strip()
        print(f"Fetching weather for {city_name}...")
        logger.info(f"Fetching weather for {city_name}...")

        if not self.api_key:
            print("OpenWeather API authentication failed - check OPENWEATHER_API_KEY")
            logger.error("OpenWeather API authentication failed - check OPENWEATHER_API_KEY")
            return self._fallback_weather(city_name, reason="Missing OPENWEATHER_API_KEY")

        params = {
            "q": city_name,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to OpenWeatherMap API: {e}")
            logger.error(f"Failed to connect to OpenWeatherMap API: {e}")
            return self._fallback_weather(city_name, reason=f"Connection Error: {str(e)}")

        if response.status_code == 200:
            data = response.json()
            print("OpenWeatherMap API status: 200")
            logger.info("OpenWeatherMap API status: 200")

            res_city = data.get("name", city_name)
            main_data = data.get("main", {})
            wind_data = data.get("wind", {})
            clouds_data = data.get("clouds", {})
            rain_data = data.get("rain", {})
            weather_arr = data.get("weather", [{}])

            temp = float(main_data.get("temp", 25.0))
            humidity = float(main_data.get("humidity", 60.0))
            pressure = float(main_data.get("pressure", 1013.0))
            wind_speed = float(wind_data.get("speed", 3.2))
            clouds = int(clouds_data.get("all", 20))
            condition = weather_arr[0].get("main", "Clear") if weather_arr else "Clear"

            # Safe rainfall extraction (1h or 3h or 0.0)
            rainfall = 0.0
            if isinstance(rain_data, dict):
                rainfall = float(rain_data.get("1h", rain_data.get("3h", 0.0)))

            print(f"Weather processed for {res_city}.")
            print(f"Temperature: {temp:.1f}°C")
            print(f"Humidity: {humidity:.1f}%")
            print(f"Rainfall: {rainfall:.1f} mm")
            print(f"Wind Speed: {wind_speed:.1f} m/s")

            return {
                "city": res_city,
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "rainfall": round(rainfall, 1),
                "wind_speed": round(wind_speed, 1),
                "pressure": round(pressure, 1),
                "clouds": clouds,
                "condition": condition,
                "source": "OpenWeatherMap Live API"
            }

        elif response.status_code == 401:
            print("OpenWeather API authentication failed - check OPENWEATHER_API_KEY")
            logger.error("OpenWeather API authentication failed - check OPENWEATHER_API_KEY")
            return self._fallback_weather(city_name, reason="OpenWeather API authentication failed - check OPENWEATHER_API_KEY")

        elif response.status_code == 404:
            print(f"City '{city_name}' not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{city_name}' not found."
            )

        else:
            err_msg = response.json().get("message", response.text) if response.headers.get("content-type", "").startswith("application/json") else response.text
            print(f"OpenWeatherMap API status ({response.status_code}): {err_msg}")
            logger.warning(f"OpenWeatherMap API status ({response.status_code}): {err_msg}")
            return self._fallback_weather(city_name, reason=f"API Status {response.status_code}")

    def _fallback_weather(self, city_name: str, reason: str) -> Dict[str, Any]:
        city_hash = sum(ord(c) for c in city_name)
        temp = round(22.0 + (city_hash % 12) + 0.4, 1)
        humidity = round(50.0 + (city_hash % 30), 1)
        rainfall = round((city_hash % 4) * 1.5, 1)
        wind_speed = round(2.5 + (city_hash % 4) * 0.8, 1)
        pressure = round(1005.0 + (city_hash % 15), 1)
        clouds = (city_hash % 60)
        condition = "Clouds" if clouds > 40 else "Clear"

        print(f"Weather processed for {city_name} ({reason}).")
        print(f"Temperature: {temp}°C | Humidity: {humidity}% | Rainfall: {rainfall} mm | Wind Speed: {wind_speed} m/s")

        return {
            "city": city_name,
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "pressure": pressure,
            "clouds": clouds,
            "condition": condition,
            "source": f"Fallback Weather Data ({reason})"
        }
