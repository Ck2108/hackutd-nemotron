"""
Weather forecast tool with mock support.
"""
import os
import json
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

USE_MOCKS = os.getenv("USE_MOCKS", "false").lower() == "true"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


def forecast(city: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
    """
    Get weather forecast for a city and date range.
    Returns: summary, high_f, low_f, rain_chance (0-1)
    """
    # Only use mocks if explicitly enabled
    if USE_MOCKS:
        return _get_mock_weather(city, start_date, end_date)
    
    # If no API key, return error status
    if not OPENWEATHER_API_KEY:
        logger.error("No OpenWeather API key configured")
        return {
            "status": "error",
            "error": "No API key configured",
            "summary": "Unknown",
            "high_f": 70,
            "low_f": 60,
            "rain_chance": 0.2
        }
    
    try:
        # OpenWeatherMap API call
        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "imperial"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process forecast data for the date range
            forecasts = data.get("list", [])
            if not forecasts:
                return _get_mock_weather(city, start_date, end_date)
            
            # Filter forecasts for the date range if specified
            if start_date:
                start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp()
                end_timestamp = datetime.combine(
                    end_date or start_date + timedelta(days=1), 
                    datetime.max.time()
                ).timestamp()
                
                relevant_forecasts = [
                    f for f in forecasts 
                    if start_timestamp <= f["dt"] <= end_timestamp
                ]
            else:
                relevant_forecasts = forecasts[:8]  # Next 24 hours
            
            if not relevant_forecasts:
                return _get_mock_weather(city, start_date, end_date)
            
            # Calculate aggregated weather
            temps = [f["main"]["temp"] for f in relevant_forecasts]
            rain_probs = [f.get("pop", 0) for f in relevant_forecasts]
            conditions = [f["weather"][0]["main"] for f in relevant_forecasts]
            
            high_f = max(temps)
            low_f = min(temps)
            rain_chance = max(rain_probs)
            
            # Determine summary
            if rain_chance > 0.5:
                summary = "Rainy"
            elif "Cloud" in conditions:
                summary = "Partly Cloudy"
            else:
                summary = "Sunny"
            
            return {
                "summary": summary,
                "high_f": round(high_f),
                "low_f": round(low_f), 
                "rain_chance": round(rain_chance, 2),
                "status": "success"
            }
        
        logger.error(f"OpenWeather API error: {response.status_code}")
        # Return error status instead of mock data
        return {
            "status": "error",
            "error": f"API returned status code {response.status_code}",
            "summary": "Unknown",
            "high_f": 70,
            "low_f": 60,
            "rain_chance": 0.2
        }
        
    except Exception as e:
        logger.error(f"Weather API call failed: {e}")
        # Return error status instead of mock data
        return {
            "status": "error",
            "error": str(e),
            "summary": "Unknown",
            "high_f": 70,
            "low_f": 60,
            "rain_chance": 0.2
        }


def _get_mock_weather(city: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
    """Mock weather data with toggle for rainy/sunny demos."""
    
    # Try to load from mock data file first
    mock_file = "data/mock/weather_next_weekend.json"
    if os.path.exists(mock_file):
        try:
            with open(mock_file, 'r') as f:
                weather_data = json.load(f)
                
            # Return appropriate weather based on city or preference
            city_lower = city.lower()
            
            # Check if there's city-specific data
            if city_lower in weather_data:
                return weather_data[city_lower]
            
            # Default to first available weather pattern
            for location, data in weather_data.items():
                return data
                
        except Exception as e:
            logger.error(f"Failed to load mock weather data: {e}")
    
    # Fallback to hardcoded mock data
    city_lower = city.lower()
    
    # Austin weather patterns
    if "austin" in city_lower:
        # Check for rainy demo mode (can be toggled via environment)
        demo_mode = os.getenv("WEATHER_DEMO_MODE", "sunny").lower()
        
        if demo_mode == "rainy":
            return {
                "summary": "Rainy",
                "high_f": 68,
                "low_f": 58,
                "rain_chance": 0.75,
                "status": "success"
            }
        else:
            return {
                "summary": "Sunny",
                "high_f": 78,
                "low_f": 62,
                "rain_chance": 0.15,
                "status": "success"
            }
    
    # Dallas weather
    elif "dallas" in city_lower:
        return {
            "summary": "Partly Cloudy",
            "high_f": 75,
            "low_f": 58,
            "rain_chance": 0.25,
            "status": "success"
        }
    
    # Houston weather
    elif "houston" in city_lower:
        return {
            "summary": "Humid",
            "high_f": 82,
            "low_f": 68,
            "rain_chance": 0.40,
            "status": "success"
        }
    
    # Default weather for any other city
    else:
        return {
            "summary": "Pleasant",
            "high_f": 74,
            "low_f": 60,
            "rain_chance": 0.20,
            "status": "success"
        }


def is_rainy(rain_chance: float) -> bool:
    """Check if weather is considered rainy (>50% chance)."""
    return rain_chance > 0.5


def is_outdoor_friendly(weather_data: Dict[str, Any]) -> bool:
    """Check if weather is good for outdoor activities."""
    return (weather_data.get("rain_chance", 0) < 0.5 and 
            weather_data.get("high_f", 70) > 50)
