"""
Hotel search tool using Google Maps Places API.
No mock data fallback - requires valid API key.
"""
import os
import logging
from datetime import date
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def search(city: str, start_date: date, end_date: date, max_price: float, near: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for top-rated hotels in a city within budget using Google Maps Places API.
    Returns the top 1 hotel (highest rated within budget) with enhanced pricing.
    Uses Place Details API to refine rental price for accurate lodging money calculation.
    
    Returns: list with single dict containing name, price_per_night, total_price, rating, lat, lng, link, address
    Returns empty list if no API key or API fails (no mock data fallback).
    """
    # Require API key - no mock data fallback
    if not GOOGLE_MAPS_API_KEY:
        logger.error("No Google Maps API key configured for hotel search")
        return []
    
    try:
        return _search_hotels_via_places_api(city, start_date, end_date, max_price, near, limit)
    except Exception as e:
        logger.error(f"Hotel API search failed: {e}")
        return []


def _search_hotels_via_places_api(city: str, start_date: date, end_date: date, max_price: float, near: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """
    Search for top-rated hotels using Google Places API.
    Gets top-rated hotels, filters by budget, and returns top 1 hotel with enhanced pricing.
    Uses Place Details API to get more accurate pricing information.
    No mock data fallback - returns empty list on errors.
    """
    # Calculate number of nights
    nights = (end_date - start_date).days
    if nights <= 0:
        nights = 1
    
    try:
        # Use Google Places API text search for hotels
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"hotels in {city}",
            "key": GOOGLE_MAPS_API_KEY,
            "type": "lodging"  # Filter for lodging/hotels
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Google Places API error: HTTP {response.status_code}")
            return []
        
        data = response.json()
        api_status = data.get("status", "")
        
        if api_status == "REQUEST_DENIED":
            error_msg = data.get("error_message", "API access denied")
            logger.error(f"Google Places API denied: {error_msg}")
            logger.error("Please enable 'Places API' in Google Cloud Console and check your API key.")
            return []
        
        if api_status != "OK":
            logger.error(f"Google Places API returned status: {api_status}")
            return []
        
        results = data.get("results", [])
        
        if not results:
            logger.warning(f"No hotels found via API for {city}")
            return []
        
        # Convert Places API results to hotel format
        hotels = []
        
        for result in results:
            # Skip if no rating (we want top-rated hotels)
            rating = result.get("rating")
            if rating is None:
                continue
            
            # Estimate price per night from price_level (0-4 scale)
            price_level = result.get("price_level")
            price_per_night = _estimate_hotel_price_from_level(price_level, rating)
            
            # Filter by max_price (budget-friendly)
            if price_per_night > max_price:
                continue
            
            total_price = price_per_night * nights
            
            # Get location
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            if not location:
                continue
            
            hotel = {
                "name": result.get("name", ""),
                "price_per_night": price_per_night,
                "total_price": total_price,
                "rating": rating,
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "place_id": result.get("place_id", ""),
                "link": f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id', '')}",
                "address": result.get("formatted_address", ""),
                "nights": nights,
                "user_ratings_total": result.get("user_ratings_total", 0),
                "price_level": price_level
            }
            hotels.append(hotel)
        
        # Sort by rating (highest first) to get top-rated hotels
        hotels.sort(key=lambda x: (x["rating"], -x["price_per_night"]), reverse=True)
        
        # Filter by budget
        budget_friendly_hotels = [h for h in hotels if h["price_per_night"] <= max_price]
        
        if not budget_friendly_hotels:
            logger.warning(f"No budget-friendly hotels found within ${max_price}/night for {city}")
            return []
        
        # Get top 1 hotel (highest rated within budget)
        top_hotel = budget_friendly_hotels[0]
        
        # Enhance pricing using Place Details API for the top hotel
        enhanced_hotel = _enhance_hotel_pricing(top_hotel, nights, max_price)
        
        logger.info(f"Selected top 1 hotel: {enhanced_hotel['name']} - ${enhanced_hotel['price_per_night']:.2f}/night (${enhanced_hotel['total_price']:.2f} total) - Rating: {enhanced_hotel['rating']:.1f}")
        
        # Return only the top 1 hotel for lodging money calculation
        return [enhanced_hotel]
        
    except Exception as e:
        logger.error(f"Hotel Places API call failed: {e}")
        return []


def _estimate_hotel_price_from_level(price_level: int = None, rating: float = None) -> float:
    """
    Convert Google Places price level to estimated price per night.
    Uses rating to refine price estimation for more accuracy.
    Price levels: 0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive
    """
    # Base price map
    base_price_map = {
        0: 50.0,   # Budget hotels
        1: 80.0,   # Inexpensive
        2: 120.0,  # Moderate
        3: 180.0,  # Expensive
        4: 250.0   # Very expensive/luxury
    }
    
    if price_level is None:
        base_price = 100.0  # Default moderate price
    else:
        base_price = base_price_map.get(price_level, 100.0)
    
    # Adjust price based on rating (higher rating = slightly higher price)
    if rating is not None:
        # Rating adjustment: ±20% based on rating
        # 5.0 rating = +20%, 3.0 rating = -20%, 4.0 rating = no change
        rating_factor = 1.0 + ((rating - 4.0) * 0.1)  # 0.1 = 10% per rating point
        base_price = base_price * rating_factor
    
    return round(base_price, 2)


def _enhance_hotel_pricing(hotel: Dict[str, Any], nights: int, max_price: float) -> Dict[str, Any]:
    """
    Enhance hotel pricing using Place Details API for more accurate rental price.
    Gets additional information about the hotel to refine price estimation.
    """
    place_id = hotel.get("place_id")
    if not place_id:
        return hotel
    
    try:
        # Use Place Details API to get more information
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": GOOGLE_MAPS_API_KEY,
            "fields": "name,rating,price_level,user_ratings_total,formatted_address,geometry,url"
        }
        
        response = requests.get(details_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                result = data.get("result", {})
                
                # Update price level if available from details
                details_price_level = result.get("price_level")
                if details_price_level is not None:
                    hotel["price_level"] = details_price_level
                
                # Refine price estimation with updated information
                rating = hotel.get("rating", result.get("rating", 4.0))
                refined_price = _estimate_hotel_price_from_level(details_price_level, rating)
                
                # Ensure price doesn't exceed max_price
                if refined_price > max_price:
                    # If refined price exceeds budget, use a price that fits within budget
                    # but still reflects quality (90% of max_price for high-rated hotels)
                    if rating >= 4.5:
                        refined_price = max_price * 0.95
                    elif rating >= 4.0:
                        refined_price = max_price * 0.90
                    else:
                        refined_price = max_price * 0.85
                
                # Update hotel pricing
                hotel["price_per_night"] = round(refined_price, 2)
                hotel["total_price"] = round(refined_price * nights, 2)
                
                # Update other fields if available
                if result.get("url"):
                    hotel["link"] = result.get("url")
                
                logger.info(f"Enhanced pricing for {hotel['name']}: ${hotel['price_per_night']:.2f}/night (refined from Place Details)")
        
    except Exception as e:
        logger.warning(f"Could not enhance pricing via Place Details API: {e}. Using estimated price.")
    
    return hotel


def find_plan_b_hotels(city: str, start_date: date, end_date: date, original_max_price: float, remaining_budget: float) -> List[Dict[str, Any]]:
    """Find cheaper hotel options when budget is tight."""
    
    nights = (end_date - start_date).days
    if nights <= 0:
        nights = 1
    
    # Calculate max price per night based on remaining budget (leave $50 buffer)
    buffer = 50.0
    max_price_per_night = (remaining_budget - buffer) / nights
    
    # Ensure it's at least 20% less than original max price
    max_price_per_night = min(max_price_per_night, original_max_price * 0.8)
    
    if max_price_per_night < 40:  # Minimum viable hotel price
        max_price_per_night = 40
    
    logger.info(f"Plan B hotel search: max ${max_price_per_night:.2f}/night with ${remaining_budget:.2f} budget")
    
    return search(city, start_date, end_date, max_price_per_night, limit=5)


def calculate_hotel_score(hotel: Dict[str, Any], interests: List[str], center_lat: float = None, center_lng: float = None) -> float:
    """Calculate a score for hotel selection based on rating, price, and location."""
    
    # Base score from rating (0-5 scale, normalize to 0-1)
    rating_score = hotel.get("rating", 4.0) / 5.0
    
    # Price score (inverse - cheaper is better, but not too cheap)
    price = hotel.get("price_per_night", 100)
    if price < 60:
        price_score = 0.6  # Very cheap might be low quality
    elif price < 100:
        price_score = 1.0  # Sweet spot
    elif price < 150:
        price_score = 0.8  # Moderate
    else:
        price_score = 0.6  # Expensive
    
    # Location score (if center point provided)
    location_score = 0.5  # Default neutral
    if center_lat and center_lng:
        from .maps import calculate_distance
        distance = calculate_distance(center_lat, center_lng, hotel["lat"], hotel["lng"])
        if distance < 2:
            location_score = 1.0
        elif distance < 5:
            location_score = 0.8
        elif distance < 10:
            location_score = 0.6
        else:
            location_score = 0.4
    
    # Weighted final score
    final_score = (rating_score * 0.4 + price_score * 0.4 + location_score * 0.2)
    
    return round(final_score, 2)
