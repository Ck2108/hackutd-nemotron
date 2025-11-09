"""
Places and POI search tool with mock support.
"""
import os
import json
import logging
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

USE_MOCKS = os.getenv("USE_MOCKS", "false").lower() == "true"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def search(query: str, near: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for places/POIs based on query and location.
    Returns: list of dicts with name, tags, rating, price, lat, lng, place_id, link
    """
    # Only use mocks if explicitly enabled
    if USE_MOCKS:
        return _get_mock_places(query, near, limit)
    
    # If no API key, return empty (will trigger generic activity generation)
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("No Google Maps API key configured. Returning empty results.")
        return []
    
    try:
        # Google Places API text search
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{query} in {near}",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            api_status = data.get("status", "")
            
            # Check for API errors
            if api_status == "REQUEST_DENIED":
                error_msg = data.get("error_message", "API access denied")
                logger.error(f"Google Places API denied: {error_msg}")
                logger.error("To use real Places API, enable 'Places API' (not legacy) in Google Cloud Console.")
                # Return empty list instead of mock data when API is denied
                return []
            
            if api_status != "OK":
                logger.error(f"Google Places API returned status: {api_status}. No results available.")
                # Return empty list instead of mock data
                return []
            
            results = data.get("results", [])
            
            if not results:
                logger.info(f"No places found for query '{query}' in {near} via API.")
                # Return empty list - let the agent handle no results
                return []
            
            places = []
            for result in results[:limit]:
                place = {
                    "name": result.get("name", ""),
                    "tags": result.get("types", []),
                    "rating": result.get("rating", 4.0),
                    "price": _estimate_price_from_level(result.get("price_level")),
                    "lat": result["geometry"]["location"]["lat"],
                    "lng": result["geometry"]["location"]["lng"], 
                    "place_id": result.get("place_id", ""),
                    "link": f"https://maps.google.com/?place_id={result.get('place_id', '')}",
                    "address": result.get("formatted_address", "")
                }
                places.append(place)
            
            return places
        
        logger.error(f"Google Places API error: {response.status_code}")
        # Return empty list instead of mock data
        return []
        
    except Exception as e:
        logger.error(f"Places API call failed: {e}")
        # Return empty list instead of mock data
        return []


def _get_mock_places(query: str, near: str, limit: int) -> List[Dict[str, Any]]:
    """Mock places data - works for any city."""
    
    # Try to load from mock data file first (Austin-specific, but works for any city)
    mock_file = "data/mock/places_austin.json"
    if os.path.exists(mock_file):
        try:
            with open(mock_file, 'r') as f:
                places_data = json.load(f)
                
            # Filter places based on query
            query_lower = query.lower()
            matching_places = []
            
            for place in places_data:
                # Check if query matches name or tags
                if (query_lower in place.get("name", "").lower() or
                    any(query_lower in tag.lower() for tag in place.get("tags", []))):
                    matching_places.append(place)
            
            return matching_places[:limit]
            
        except Exception as e:
            logger.error(f"Failed to load mock places data: {e}")
    
    # Fallback to hardcoded mock data
    query_lower = query.lower()
    near_lower = near.lower()
    
    all_places = []
    
    # BBQ places
    if "bbq" in query_lower or "barbecue" in query_lower:
        all_places.extend([
            {
                "name": "Franklin Barbecue",
                "tags": ["BBQ", "restaurant"],
                "rating": 4.6,
                "price": 25.0,
                "lat": 30.2701,
                "lng": -97.7374,
                "place_id": "franklin_bbq",
                "link": "https://franklinbbq.com",
                "address": "900 E 11th St, Austin, TX 78702"
            },
            {
                "name": "la Barbecue",
                "tags": ["BBQ", "restaurant"],
                "rating": 4.4,
                "price": 20.0,
                "lat": 30.2580,
                "lng": -97.7386,
                "place_id": "la_barbecue",
                "link": "https://labarbecue.com",
                "address": "2401 E Cesar Chavez St, Austin, TX 78702"
            },
            {
                "name": "Stubb's Bar-B-Q",
                "tags": ["BBQ", "restaurant", "live music", "venue"],
                "rating": 4.2,
                "price": 22.0,
                "lat": 30.2634,
                "lng": -97.7354,
                "place_id": "stubbs_bbq",
                "link": "https://stubbsaustin.com",
                "address": "801 Red River St, Austin, TX 78701"
            }
        ])
    
    # Live music venues
    if "music" in query_lower or "live" in query_lower:
        all_places.extend([
            {
                "name": "The Continental Club",
                "tags": ["live music", "venue", "bar"],
                "rating": 4.5,
                "price": 15.0,
                "lat": 30.2625,
                "lng": -97.7506,
                "place_id": "continental_club",
                "link": "https://continentalclub.com",
                "address": "1315 S Congress Ave, Austin, TX 78704"
            },
            {
                "name": "Antone's Nightclub",
                "tags": ["live music", "venue", "blues"],
                "rating": 4.4,
                "price": 20.0,
                "lat": 30.2669,
                "lng": -97.7431,
                "place_id": "antones",
                "link": "https://antonesnightclub.com",
                "address": "305 E 5th St, Austin, TX 78701"
            },
            {
                "name": "Stubb's Bar-B-Q",
                "tags": ["BBQ", "restaurant", "live music", "venue"],
                "rating": 4.2,
                "price": 22.0,
                "lat": 30.2634,
                "lng": -97.7354,
                "place_id": "stubbs_bbq",
                "link": "https://stubbsaustin.com",
                "address": "801 Red River St, Austin, TX 78701"
            },
            {
                "name": "Saxon Pub",
                "tags": ["live music", "venue", "songwriter"],
                "rating": 4.6,
                "price": 12.0,
                "lat": 30.2515,
                "lng": -97.7697,
                "place_id": "saxon_pub",
                "link": "https://saxonpub.com",
                "address": "1320 S Lamar Blvd, Austin, TX 78704"
            }
        ])
    
    # Parks and outdoor activities
    if "park" in query_lower or "outdoor" in query_lower:
        all_places.extend([
            {
                "name": "Zilker Park",
                "tags": ["park", "outdoor", "activities"],
                "rating": 4.5,
                "price": 0.0,
                "lat": 30.2672,
                "lng": -97.7731,
                "place_id": "zilker_park",
                "link": "https://austintexas.gov/department/zilker-metropolitan-park",
                "address": "2100 Barton Springs Rd, Austin, TX 78746"
            },
            {
                "name": "Barton Springs Pool",
                "tags": ["swimming", "park", "outdoor"],
                "rating": 4.4,
                "price": 5.0,
                "lat": 30.2641,
                "lng": -97.7731,
                "place_id": "barton_springs",
                "link": "https://austintexas.gov/department/barton-springs-pool",
                "address": "2201 Barton Springs Rd, Austin, TX 78746"
            }
        ])
    
    # Museums and indoor activities
    if "museum" in query_lower or "indoor" in query_lower:
        all_places.extend([
            {
                "name": "Bullock Texas State History Museum",
                "tags": ["museum", "history", "indoor"],
                "rating": 4.3,
                "price": 15.0,
                "lat": 30.2808,
                "lng": -97.7391,
                "place_id": "bullock_museum",
                "link": "https://thestoryoftexas.com",
                "address": "1800 Congress Ave, Austin, TX 78701"
            },
            {
                "name": "Contemporary Austin",
                "tags": ["museum", "art", "indoor"],
                "rating": 4.2,
                "price": 10.0,
                "lat": 30.2648,
                "lng": -97.7678,
                "place_id": "contemporary_austin",
                "link": "https://thecontemporaryaustin.org",
                "address": "700 Congress Ave, Austin, TX 78701"
            }
        ])
    
    # Coffee shops
    if "coffee" in query_lower:
        all_places.extend([
            {
                "name": "Sightglass Coffee",
                "tags": ["coffee", "cafe"],
                "rating": 4.4,
                "price": 8.0,
                "lat": 30.2651,
                "lng": -97.7451,
                "place_id": "sightglass_coffee",
                "link": "https://sightglasscoffee.com",
                "address": "111 W 2nd St, Austin, TX 78701"
            },
            {
                "name": "Radio Coffee & Beer",
                "tags": ["coffee", "beer", "cafe"],
                "rating": 4.3,
                "price": 10.0,
                "lat": 30.2515,
                "lng": -97.7595,
                "place_id": "radio_coffee",
                "link": "https://radiocoffeeandbeer.com",
                "address": "4204 Menchaca Rd, Austin, TX 78704"
            }
        ])
    
    # Remove duplicates based on place_id
    seen_ids = set()
    unique_places = []
    for place in all_places:
        if place["place_id"] not in seen_ids:
            unique_places.append(place)
            seen_ids.add(place["place_id"])
    
    return unique_places[:limit]


def _estimate_price_from_level(price_level: int = None) -> float:
    """Convert Google Places price level to estimated cost per person."""
    if price_level is None:
        return 15.0  # Default moderate price
    
    price_map = {
        0: 0.0,   # Free (parks, public spaces, etc.)
        1: 10.0,  # Inexpensive
        2: 20.0,  # Moderate
        3: 35.0,  # Expensive
        4: 50.0   # Very expensive
    }
    
    return price_map.get(price_level, 15.0)


def find_overlapping_interests(places: List[Dict[str, Any]], interests: List[str]) -> List[Dict[str, Any]]:
    """Find places that satisfy multiple interests."""
    overlapping = []
    
    for place in places:
        place_tags = [tag.lower() for tag in place.get("tags", [])]
        place_name = place.get("name", "").lower()
        
        matching_interests = 0
        for interest in interests:
            interest_lower = interest.lower()
            if (interest_lower in place_name or 
                any(interest_lower in tag for tag in place_tags)):
                matching_interests += 1
        
        if matching_interests >= 2:
            place["interest_matches"] = matching_interests
            overlapping.append(place)
    
    # Sort by number of matching interests
    return sorted(overlapping, key=lambda x: x.get("interest_matches", 0), reverse=True)


def filter_by_location(places: List[Dict[str, Any]], center_lat: float, center_lng: float, max_distance_miles: float = 5.0) -> List[Dict[str, Any]]:
    """Filter places within a certain distance of a center point."""
    from .maps import calculate_distance
    
    nearby_places = []
    for place in places:
        distance = calculate_distance(center_lat, center_lng, place["lat"], place["lng"])
        if distance <= max_distance_miles:
            place["distance_from_center"] = round(distance, 1)
            nearby_places.append(place)
    
    # Sort by distance
    return sorted(nearby_places, key=lambda x: x.get("distance_from_center", 0))
