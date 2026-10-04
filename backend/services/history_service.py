"""
AgriSmartAI - Prediction History Service & SQLite Persistence Module
Manages creation, storage, retrieval, and deletion of prediction history records.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AgriSmartAI.HistoryService")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback.db")

def init_history_db():
    """Initializes the prediction_history table in the SQLite database if it does not exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                city TEXT NOT NULL,
                soil_n REAL,
                soil_p REAL,
                soil_k REAL,
                soil_ph REAL,
                soil_moisture REAL,
                temperature REAL,
                humidity REAL,
                rainfall REAL,
                wind_speed REAL,
                selected_crop TEXT,
                recommended_crop TEXT,
                recommended_crops_json TEXT,
                confidence_pct REAL,
                predicted_yield REAL,
                fertilizer TEXT,
                irrigation_level TEXT,
                irrigation_json TEXT,
                raw_payload_json TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Prediction History SQLite table initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing prediction_history table: {e}")

# Initialize table at module import time
init_history_db()

def save_prediction_history(request_dict: Dict[str, Any], advisory_result: Dict[str, Any]) -> Optional[int]:
    """
    Safely saves a copy of a successful prediction result into SQLite database.
    Does not raise exceptions to ensure API endpoint isolation.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        city = (
            advisory_result.get("city")
            or request_dict.get("city")
            or "Unknown Location"
        )
        
        # Extract Soil inputs
        soil_n = float(request_dict.get("N", request_dict.get("Nitrogen", 50.0)))
        soil_p = float(request_dict.get("P", request_dict.get("Phosphorus", 50.0)))
        soil_k = float(request_dict.get("K", request_dict.get("Potassium", 50.0)))
        soil_ph = float(request_dict.get("pH", request_dict.get("ph", 6.5)))
        soil_moisture = float(request_dict.get("Soil_Moisture", request_dict.get("soil_moisture", 45.0)))
        
        # Extract Weather inputs
        weather = advisory_result.get("weather_summary") or advisory_result.get("weather") or {}
        if isinstance(weather, dict):
            temp = float(weather.get("temperature", weather.get("temperature_c", request_dict.get("temperature", 25.0))))
            humidity = float(weather.get("humidity", weather.get("humidity_pct", request_dict.get("humidity", 60.0))))
            rainfall = float(weather.get("rainfall", weather.get("rainfall_mm", request_dict.get("rainfall", 0.0))))
            wind_speed = float(weather.get("wind_speed", weather.get("wind_speed_ms", request_dict.get("wind_speed", 0.0))))
        else:
            temp = float(request_dict.get("temperature", 25.0))
            humidity = float(request_dict.get("humidity", 60.0))
            rainfall = float(request_dict.get("rainfall", 0.0))
            wind_speed = float(request_dict.get("wind_speed", 0.0))

        selected_crop = advisory_result.get("selected_crop") or request_dict.get("selected_crop") or ""
        
        # Extract Recommended Crops
        rec_crops = advisory_result.get("recommended_crops") or []
        if rec_crops and isinstance(rec_crops, list) and len(rec_crops) > 0:
            if isinstance(rec_crops[0], dict):
                recommended_crop = rec_crops[0].get("crop", "Rice")
                confidence_pct = float(rec_crops[0].get("confidence_pct", 92.05))
            else:
                recommended_crop = str(rec_crops[0])
                confidence_pct = 92.05
            rec_crops_names = [c.get("crop") if isinstance(c, dict) else str(c) for c in rec_crops]
        else:
            recommended_crop = advisory_result.get("recommended_crop") or "Rice"
            confidence_pct = float(advisory_result.get("recommended_crop_confidence") or 92.05)
            rec_crops_names = [recommended_crop]

        predicted_yield = advisory_result.get("predicted_yield_tons_per_ha")
        if predicted_yield is not None:
            predicted_yield = float(predicted_yield)

        fertilizer = advisory_result.get("fertilizer_recommendation") or "NPK Strategy"
        
        irr_obj = advisory_result.get("irrigation_recommendation") or {}
        if isinstance(irr_obj, dict):
            irrigation_level = irr_obj.get("level", "Moderate")
            irrigation_json = json.dumps(irr_obj)
        else:
            irrigation_level = str(irr_obj)
            irrigation_json = json.dumps({"level": irrigation_level})

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prediction_history (
                timestamp, city, soil_n, soil_p, soil_k, soil_ph, soil_moisture,
                temperature, humidity, rainfall, wind_speed,
                selected_crop, recommended_crop, recommended_crops_json, confidence_pct,
                predicted_yield, fertilizer, irrigation_level, irrigation_json, raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, city, soil_n, soil_p, soil_k, soil_ph, soil_moisture,
            temp, humidity, rainfall, wind_speed,
            selected_crop, recommended_crop, json.dumps(rec_crops_names), confidence_pct,
            predicted_yield, fertilizer, irrigation_level, irrigation_json, json.dumps(advisory_result)
        ))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        logger.info(f"Prediction history saved successfully. Record ID: {record_id}")
        return record_id
    except Exception as e:
        logger.error(f"Failed to save prediction history to database: {e}")
        return None

def get_all_prediction_history() -> List[Dict[str, Any]]:
    """Retrieves all historical prediction records from SQLite database ordered by newest first."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, city, soil_n, soil_p, soil_k, soil_ph, soil_moisture,
                   temperature, humidity, rainfall, wind_speed,
                   selected_crop, recommended_crop, recommended_crops_json, confidence_pct,
                   predicted_yield, fertilizer, irrigation_level, irrigation_json, raw_payload_json
            FROM prediction_history ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            try:
                rec_crops_list = json.loads(r[14]) if r[14] else [r[13]]
            except Exception:
                rec_crops_list = [r[13]] if r[13] else []

            try:
                irr_data = json.loads(r[19]) if r[19] else {"level": r[18] or "Moderate"}
            except Exception:
                irr_data = {"level": r[18] or "Moderate"}

            item = {
                "id": r[0],
                "timestamp": r[1],
                "city": r[2],
                "location": r[2],
                "soil": {
                    "N": r[3],
                    "P": r[4],
                    "K": r[5],
                    "ph": r[6],
                    "soil_moisture": r[7]
                },
                "weather": {
                    "temperature": r[8],
                    "humidity": r[9],
                    "rainfall": r[10],
                    "wind_speed": r[11]
                },
                "selected_crop": r[12] if r[12] else r[13],
                "recommended_crop": r[13],
                "recommended_crops": rec_crops_list,
                "confidence_pct": r[15],
                "predicted_yield": r[16],
                "predicted_yield_tons_per_ha": r[16],
                "fertilizer": r[17],
                "fertilizer_recommendation": r[17],
                "irrigation": irr_data,
                "irrigation_level": r[18]
            }
            result.append(item)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch prediction history: {e}")
        return []

def delete_prediction_history_item(record_id: int) -> bool:
    """Deletes a single prediction history record by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prediction_history WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to delete prediction history record {record_id}: {e}")
        return False

def clear_all_prediction_history() -> bool:
    """Clears all records from the prediction history table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prediction_history")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to clear prediction history: {e}")
        return False
