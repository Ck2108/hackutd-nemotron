"""
Maps and directions tool with mock support.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

USE_MOCKS = os.getenv("USE_MOCKS", "false").lower() == "true"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def find_directions(origin: str, destination: str) -> Dict[str, Any]:
    """
    Find directions between two locations.
    Returns: duration_minutes, distance_miles, gas_estimate, polyline
    """
    # Only use mocks if explicitly enabled
    if USE_MOCKS:
        return _get_mock_directions(origin, destination)
    
    # If no API key, return error status
    if not GOOGLE_MAPS_API_KEY:
        logger.error("No Google Maps API key configured")
        return {
            "status": "error",
            "error": "No API key configured",
            "duration_minutes": 0,
            "distance_miles": 0,
            "gas_estimate": 0
        }
    
    try:
        # Google Maps Directions API call
        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "key": GOOGLE_MAPS_API_KEY,
            "units": "imperial"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]
                
                duration_minutes = leg["duration"]["value"] // 60
                distance_miles = leg["distance"]["value"] * 0.000621371  # meters to miles
                
                # Simple gas estimate: $3.50/gallon, 25 mpg average
                gas_estimate = (distance_miles / 25.0) * 3.50
                
                return {
                    "duration_minutes": duration_minutes,
                    "distance_miles": round(distance_miles, 1),
                    "gas_estimate": round(gas_estimate, 2),
                    "polyline": route.get("overview_polyline", {}).get("points", ""),
                    "status": "success"
                }
        
        logger.error(f"Google Maps API error: {response.status_code}")
        # Return error status instead of mock data
        return {
            "status": "error",
            "error": f"API returned status code {response.status_code}",
            "duration_minutes": 0,
            "distance_miles": 0,
            "gas_estimate": 0
        }
    
    except Exception as e:
        logger.error(f"Maps API call failed: {e}")
        # Return error status instead of mock data
        return {
            "status": "error",
            "error": str(e),
            "duration_minutes": 0,
            "distance_miles": 0,
            "gas_estimate": 0
        }


def _get_mock_directions(origin: str, destination: str) -> Dict[str, Any]:
    """Mock directions data for common routes."""
    
    # Normalize locations for matching
    origin_lower = origin.lower()
    destination_lower = destination.lower()
    
    # Dallas to Austin (most common case)
    if ("dallas" in origin_lower and "austin" in destination_lower) or \
       ("austin" in origin_lower and "dallas" in destination_lower):
        return {
            "duration_minutes": 195,  # 3 hours 15 minutes
            "distance_miles": 195.0,
            "gas_estimate": 27.30,  # ~$27 for gas
            "polyline": "mock_polyline_data",
            "status": "success"
        }
    
    # Houston to Austin
    elif ("houston" in origin_lower and "austin" in destination_lower) or \
         ("austin" in origin_lower and "houston" in destination_lower):
        return {
            "duration_minutes": 165,  # 2 hours 45 minutes
            "distance_miles": 165.0,
            "gas_estimate": 23.10,
            "polyline": "mock_polyline_data",
            "status": "success"
        }
    
    # San Antonio to Austin
    elif ("san antonio" in origin_lower and "austin" in destination_lower) or \
         ("austin" in origin_lower and "san antonio" in destination_lower):
        return {
            "duration_minutes": 80,  # 1 hour 20 minutes
            "distance_miles": 80.0,
            "gas_estimate": 11.20,
            "polyline": "mock_polyline_data",
            "status": "success"
        }
    
    # Default estimate for any other route
    else:
        # Rough estimate based on typical distances
        return {
            "duration_minutes": 120,  # 2 hours default
            "distance_miles": 120.0,
            "gas_estimate": 16.80,
            "polyline": "mock_polyline_data",
            "status": "success"
        }


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula."""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in miles
    r = 3956
    
    return c * r


def estimate_travel_time(distance_miles: float) -> int:
    """Estimate travel time in minutes based on distance."""
    # Assume average city speed of 25 mph
    return int((distance_miles / 25.0) * 60)


def geocode_city(city_name: str) -> Tuple[float, float]:
    """
    Get latitude and longitude for a city name using Google Maps Geocoding API.
    Falls back to a lookup table if API is unavailable.
    
    Returns:
        tuple: (latitude, longitude) or (30.2672, -97.7431) as default (Austin)
    """
    # Common city coordinates lookup
    city_coordinates = {
        "austin": (30.2672, -97.7431),
        "austin, tx": (30.2672, -97.7431),
        "dallas": (32.7767, -96.7970),
        "dallas, tx": (32.7767, -96.7970),
        "houston": (29.7604, -95.3698),
        "houston, tx": (29.7604, -95.3698),
        "san antonio": (29.4241, -98.4936),
        "san antonio, tx": (29.4241, -98.4936),
        "new york": (40.7128, -74.0060),
        "new york, ny": (40.7128, -74.0060),
        "los angeles": (34.0522, -118.2437),
        "los angeles, ca": (34.0522, -118.2437),
        "chicago": (41.8781, -87.6298),
        "chicago, il": (41.8781, -87.6298),
        "miami": (25.7617, -80.1918),
        "miami, fl": (25.7617, -80.1918),
        "seattle": (47.6062, -122.3321),
        "seattle, wa": (47.6062, -122.3321),
        "denver": (39.7392, -104.9903),
        "denver, co": (39.7392, -104.9903),
        "phoenix": (33.4484, -112.0740),
        "phoenix, az": (33.4484, -112.0740),
    }
    
    # Try lookup table first
    city_lower = city_name.lower().strip()
    if city_lower in city_coordinates:
        return city_coordinates[city_lower]
    
    # Try Google Geocoding API if available
    if not USE_MOCKS and GOOGLE_MAPS_API_KEY:
        try:
            base_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": city_name,
                "key": GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    lat = location["lat"]
                    lng = location["lng"]
                    logger.info(f"Geocoded {city_name} to ({lat}, {lng})")
                    return (lat, lng)
        except Exception as e:
            logger.warning(f"Geocoding API failed for {city_name}: {e}")
    
    # Fallback: try to extract state and match
    if "," in city_lower:
        city_part = city_lower.split(",")[0].strip()
        if city_part in city_coordinates:
            return city_coordinates[city_part]
    
    # Default fallback (Austin coordinates)
    logger.warning(f"Could not geocode {city_name}, using default coordinates")
    return (30.2672, -97.7431)
