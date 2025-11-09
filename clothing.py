"""
Clothing suggestion tool with LLM-powered recommendations based on weather and seasons.
"""
import os
import json
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from agent.llm import llm_client

logger = logging.getLogger(__name__)


def get_season_from_date(trip_date: date) -> str:
    """
    Determine season from date.
    
    Returns: "spring", "summer", "fall", "winter"
    """
    month = trip_date.month
    
    # Northern Hemisphere seasons
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"


def get_seasons_from_date_range(start_date: date, end_date: date) -> List[str]:
    """
    Get all seasons covered by the date range.
    
    Returns: List of seasons (e.g., ["fall", "winter"] for Nov-Dec trip)
    """
    seasons = set()
    current_date = start_date
    
    while current_date <= end_date:
        season = get_season_from_date(current_date)
        seasons.add(season)
        # Move to next month to check for season changes
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
        if current_date > end_date:
            break
    
    return sorted(list(seasons), key=lambda s: ["winter", "spring", "summer", "fall"].index(s))


def get_destination_climate_zone(destination: str) -> str:
    """
    Determine the climate zone of a destination based on location.
    
    Returns: "tropical", "desert", "west_coast", "southern", "northern", "mountain", "coastal_east"
    """
    destination_lower = destination.lower()
    
    # West Coast (mild winters, moderate summers)
    west_coast_cities = [
        "los angeles", "san francisco", "san diego", "seattle", "portland", 
        "sacramento", "oakland", "san jose", "fresno", "long beach",
        "california", "oregon", "washington"
    ]
    
    # Southern states (hot summers, mild winters)
    southern_cities = [
        "austin", "houston", "dallas", "atlanta", "miami", "orlando",
        "tampa", "charleston", "nashville", "memphis", "new orleans",
        "phoenix", "las vegas", "tucson", "albuquerque",
        "texas", "florida", "georgia", "arizona", "nevada"
    ]
    
    # Northern states (cold winters, moderate summers)
    northern_cities = [
        "chicago", "boston", "minneapolis", "detroit", "milwaukee",
        "buffalo", "cleveland", "pittsburgh", "minnesota", "michigan",
        "wisconsin", "massachusetts", "illinois", "ohio", "pennsylvania"
    ]
    
    # East Coast (varies by region)
    east_coast_cities = [
        "new york", "philadelphia", "baltimore", "washington", "virginia",
        "maryland", "north carolina", "south carolina", "connecticut",
        "rhode island", "new jersey", "delaware"
    ]
    
    # Desert regions
    desert_regions = [
        "phoenix", "las vegas", "tucson", "palm springs", "mojave"
    ]
    
    # Mountain regions (cooler, more variable)
    mountain_regions = [
        "denver", "salt lake city", "boise", "colorado", "utah", "wyoming",
        "montana", "idaho"
    ]
    
    # Tropical regions
    tropical_regions = [
        "miami", "key west", "honolulu", "hawaii", "puerto rico"
    ]
    
    # Check categories
    if any(city in destination_lower for city in tropical_regions):
        return "tropical"
    elif any(city in destination_lower for city in desert_regions):
        return "desert"
    elif any(city in destination_lower for city in west_coast_cities):
        return "west_coast"
    elif any(city in destination_lower for city in southern_cities):
        return "southern"
    elif any(city in destination_lower for city in mountain_regions):
        return "mountain"
    elif any(city in destination_lower for city in northern_cities):
        return "northern"
    elif any(city in destination_lower for city in east_coast_cities):
        return "coastal_east"
    else:
        # Default to moderate climate
        return "moderate"


def get_season_weather_profile(season: str, destination: str = "", climate_zone: str = None) -> Dict[str, Any]:
    """
    Get typical weather profile for a season and destination based on climate zone.
    
    Args:
        season: Season name (spring, summer, fall, winter)
        destination: Destination city/state name
        climate_zone: Climate zone (optional, will be determined if not provided)
    
    Returns: Dictionary with estimated temperature range and rain probability
    """
    if climate_zone is None:
        climate_zone = get_destination_climate_zone(destination)
    
    # Climate zone-based weather profiles
    profiles = {
        "tropical": {
            "winter": {"high_f": 82, "low_f": 68, "rain_chance": 0.25, "summary": "Warm Winter"},
            "spring": {"high_f": 85, "low_f": 72, "rain_chance": 0.30, "summary": "Warm Spring"},
            "summer": {"high_f": 88, "low_f": 78, "rain_chance": 0.40, "summary": "Hot & Humid Summer"},
            "fall": {"high_f": 84, "low_f": 70, "rain_chance": 0.35, "summary": "Warm Fall"}
        },
        "desert": {
            "winter": {"high_f": 68, "low_f": 45, "rain_chance": 0.15, "summary": "Mild Winter"},
            "spring": {"high_f": 85, "low_f": 60, "rain_chance": 0.10, "summary": "Warm Spring"},
            "summer": {"high_f": 105, "low_f": 80, "rain_chance": 0.20, "summary": "Very Hot Summer"},
            "fall": {"high_f": 88, "low_f": 65, "rain_chance": 0.15, "summary": "Warm Fall"}
        },
        "west_coast": {
            "winter": {"high_f": 68, "low_f": 52, "rain_chance": 0.35, "summary": "Mild & Rainy Winter"},
            "spring": {"high_f": 72, "low_f": 56, "rain_chance": 0.30, "summary": "Mild Spring"},
            "summer": {"high_f": 78, "low_f": 62, "rain_chance": 0.05, "summary": "Warm & Dry Summer"},
            "fall": {"high_f": 75, "low_f": 60, "rain_chance": 0.15, "summary": "Warm Fall"}  # California is warm in November
        },
        "southern": {
            "winter": {"high_f": 65, "low_f": 45, "rain_chance": 0.30, "summary": "Mild Winter"},
            "spring": {"high_f": 78, "low_f": 58, "rain_chance": 0.40, "summary": "Warm & Rainy Spring"},
            "summer": {"high_f": 92, "low_f": 72, "rain_chance": 0.35, "summary": "Hot & Humid Summer"},
            "fall": {"high_f": 80, "low_f": 60, "rain_chance": 0.25, "summary": "Warm Fall"}
        },
        "northern": {
            "winter": {"high_f": 32, "low_f": 18, "rain_chance": 0.35, "summary": "Cold Winter"},
            "spring": {"high_f": 58, "low_f": 40, "rain_chance": 0.45, "summary": "Cool & Rainy Spring"},
            "summer": {"high_f": 82, "low_f": 62, "rain_chance": 0.30, "summary": "Moderate Summer"},
            "fall": {"high_f": 62, "low_f": 42, "rain_chance": 0.40, "summary": "Cool Fall"}
        },
        "coastal_east": {
            "winter": {"high_f": 42, "low_f": 28, "rain_chance": 0.40, "summary": "Cold & Wet Winter"},
            "spring": {"high_f": 62, "low_f": 46, "rain_chance": 0.42, "summary": "Cool Spring"},
            "summer": {"high_f": 83, "low_f": 66, "rain_chance": 0.35, "summary": "Warm & Humid Summer"},
            "fall": {"high_f": 62, "low_f": 46, "rain_chance": 0.40, "summary": "Cool Fall"}  # New York is cooler in November
        },
        "mountain": {
            "winter": {"high_f": 40, "low_f": 20, "rain_chance": 0.30, "summary": "Cold Winter"},
            "spring": {"high_f": 60, "low_f": 38, "rain_chance": 0.35, "summary": "Cool Spring"},
            "summer": {"high_f": 82, "low_f": 55, "rain_chance": 0.25, "summary": "Warm Days, Cool Nights"},
            "fall": {"high_f": 65, "low_f": 40, "rain_chance": 0.30, "summary": "Cool Fall"}
        },
        "moderate": {
            "winter": {"high_f": 50, "low_f": 35, "rain_chance": 0.35, "summary": "Moderate Winter"},
            "spring": {"high_f": 68, "low_f": 50, "rain_chance": 0.42, "summary": "Mild Spring"},
            "summer": {"high_f": 85, "low_f": 68, "rain_chance": 0.28, "summary": "Warm Summer"},
            "fall": {"high_f": 72, "low_f": 52, "rain_chance": 0.32, "summary": "Mild Fall"}
        }
    }
    
    # Get profile for the climate zone and season
    if climate_zone in profiles and season in profiles[climate_zone]:
        return profiles[climate_zone][season].copy()
    else:
        # Fallback to moderate climate
        return profiles["moderate"][season].copy()


def suggest_clothing(
    weather_data: Optional[Dict[str, Any]] = None,
    gender: str = "both",
    destination: str = "",
    days: int = 3,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Generate clothing suggestions based on weather and/or season using LLM.
    
    Args:
        weather_data: Optional weather forecast data with summary, high_f, low_f, rain_chance
        gender: "male", "female", or "both"
        destination: Destination city name
        days: Number of days for the trip
        start_date: Trip start date (for season detection)
        end_date: Trip end date (for season detection)
    
    Returns:
        Dictionary with clothing suggestions for male and/or female with color palettes
    """
    try:
        # Determine climate zone from destination
        climate_zone = get_destination_climate_zone(destination)
        
        # Determine season(s) from date range
        seasons = []
        primary_season = None
        if start_date and end_date:
            seasons = get_seasons_from_date_range(start_date, end_date)
            primary_season = seasons[0]  # Use first season as primary
        elif start_date:
            primary_season = get_season_from_date(start_date)
            seasons = [primary_season]
        
        # Use weather data if available, otherwise use location and season-based estimates
        if weather_data and weather_data.get("status") == "success":
            summary = weather_data.get("summary", "Pleasant")
            high_f = weather_data.get("high_f", 70)
            low_f = weather_data.get("low_f", 60)
            rain_chance = weather_data.get("rain_chance", 0.2)
            weather_source = "weather_api"
        else:
            # Use location and season-based weather profile
            if primary_season:
                season_profile = get_season_weather_profile(primary_season, destination, climate_zone)
                summary = season_profile["summary"]
                high_f = season_profile["high_f"]
                low_f = season_profile["low_f"]
                rain_chance = season_profile["rain_chance"]
                
                # If trip spans multiple seasons, adjust for range
                if len(seasons) > 1:
                    # Average the temperatures across seasons
                    all_profiles = [get_season_weather_profile(s, destination, climate_zone) for s in seasons]
                    high_f = int(sum(p["high_f"] for p in all_profiles) / len(all_profiles))
                    low_f = int(sum(p["low_f"] for p in all_profiles) / len(all_profiles))
                    rain_chance = sum(p["rain_chance"] for p in all_profiles) / len(all_profiles)
                    season_names = ", ".join([s.title() for s in seasons])
                    summary = f"{summary} (spanning {season_names})"
                    weather_source = f"season_{climate_zone}_{'-'.join(seasons)}"
                else:
                    weather_source = f"season_{climate_zone}_{primary_season}"
            else:
                # Default to moderate weather for the destination's climate zone
                default_profile = get_season_weather_profile("spring", destination, climate_zone)
                summary = default_profile["summary"]
                high_f = default_profile["high_f"]
                low_f = default_profile["low_f"]
                rain_chance = default_profile["rain_chance"]
                weather_source = f"default_{climate_zone}"
        
        # Build enhanced prompt for trendy/fashionable suggestions
        season_context = ""
        if len(seasons) > 1:
            season_names = " and ".join([s.title() for s in seasons])
            season_context = f" during {season_names} seasons (trip spans multiple seasons)"
        elif primary_season:
            season_context = f" during {primary_season.title()} season"
        
        climate_context = f" The destination ({destination}) has a {climate_zone.replace('_', ' ')} climate,"
        if climate_zone == "west_coast":
            climate_context += " which means mild winters and moderate summers (like California)."
        elif climate_zone == "southern":
            climate_context += " which means hot summers and mild winters."
        elif climate_zone == "northern":
            climate_context += " which means cold winters and moderate summers."
        elif climate_zone == "tropical":
            climate_context += " which means warm weather year-round."
        elif climate_zone == "desert":
            climate_context += " which means very hot summers and mild winters."
        else:
            climate_context += " which influences the clothing needs."
        
        prompt = f"""You are a renowned fashion stylist and trend expert. Create trendy, fashionable, and stylish clothing recommendations for a {days}-day trip to {destination}{season_context}.{climate_context}

WEATHER & SEASONAL CONTEXT:
- Season(s): {', '.join([s.title() for s in seasons]) if seasons else (primary_season.title() if primary_season else 'Not specified')}
- Climate Zone: {climate_zone.replace('_', ' ').title()}
- Weather Summary: {summary}
- Temperature Range: {low_f}°F - {high_f}°F
- Rain Probability: {int(rain_chance * 100)}%

FASHION REQUIREMENTS:
1. **TRENDY & MODERN**: Include current fashion trends, contemporary styles, and modern aesthetics
2. **WEATHER-APPROPRIATE**: Consider temperature, rain probability, and seasonal conditions
3. **VERSATILE & MIX-AND-MATCH**: Suggest pieces that can be combined in multiple ways
4. **STYLISH COLOR PALETTE**: Provide a cohesive, fashionable color palette with specific color names and hex codes (4-6 colors that work beautifully together)
5. **LAYERING EXPERTISE**: Suggest smart layering options for temperature variations
6. **FASHION-FORWARD ACCESSORIES**: Include trendy accessories that elevate the outfits
7. **PRACTICAL YET STYLISH**: Balance fashion with practicality for travel

GENDER: {gender if gender != "both" else "Both male and female travelers"}

FOR EACH GENDER, PROVIDE:
- **Trendy Outfit Items**: Specific, fashionable clothing pieces (tops, bottoms, outerwear, footwear, accessories)
- **Color Palette**: 4-6 trendy colors with names and hex codes that create a cohesive, stylish wardrobe
- **Style Notes**: Fashion-forward advice on how to style the pieces, current trends, and styling tips
- **Special Items**: Trendy accessories and special items needed (umbrella, hat, sunglasses, etc.)

Make the suggestions fashionable, trendy, and reflect current style trends while being practical for travel. Think like a professional stylist creating a curated wardrobe."""

        # Get LLM completion
        response = llm_client.get_completion(prompt, max_tokens=2500)
        
        # Parse response and create structured output
        suggestions = _parse_llm_response(response, weather_data or {}, gender, high_f, low_f, rain_chance, primary_season)
        
        return {
            "status": "success",
            "weather_summary": summary,
            "temperature_range": f"{low_f}°F - {high_f}°F",
            "rain_chance": rain_chance,
            "season": primary_season,
            "seasons": seasons if seasons else [primary_season] if primary_season else [],
            "climate_zone": climate_zone,
            "weather_source": weather_source,
            "suggestions": suggestions,
            "raw_llm_response": response
        }
        
    except Exception as e:
        logger.error(f"Failed to generate clothing suggestions: {e}")
        # Use location and season-based fallback
        climate_zone = get_destination_climate_zone(destination)
        primary_season = get_season_from_date(start_date) if start_date else None
        if primary_season:
            season_profile = get_season_weather_profile(primary_season, destination, climate_zone)
        else:
            season_profile = {"high_f": 70, "low_f": 60, "rain_chance": 0.25, "summary": "Pleasant"}
        return _get_fallback_suggestions(
            season_profile, 
            gender, 
            season_profile["high_f"], 
            season_profile["low_f"], 
            season_profile["rain_chance"],
            primary_season,
            destination
        )


def _parse_llm_response(
    response: str,
    weather_data: Dict[str, Any],
    gender: str,
    high_f: float,
    low_f: float,
    rain_chance: float,
    season: Optional[str] = None
) -> Dict[str, Any]:
    """Parse LLM response and extract structured clothing suggestions."""
    
    suggestions = {}
    
    # Determine if we need suggestions for both genders
    genders_to_process = ["male", "female"] if gender == "both" else [gender]
    
    # Extract colors and items from the entire response (LLM might not separate by gender clearly)
    all_colors = _extract_colors(response, season)
    
    for gen in genders_to_process:
        # Try to extract gender-specific content from LLM response
        gen_lower = gen.lower()
        response_lower = response.lower()
        
        # Extract color palette - enhance with season-based colors if LLM didn't provide enough
        if all_colors and len(all_colors) >= 4:
            colors = all_colors[:6]  # Use LLM colors
        else:
            # Use season-based trendy colors
            colors = _get_default_colors_for_weather("", season)
            # Enhance with any colors found in LLM response
            if all_colors:
                existing_hex = {c["hex"] for c in colors}
                for llm_color in all_colors:
                    if llm_color["hex"] not in existing_hex and len(colors) < 6:
                        colors.append(llm_color)
        
        # Extract outfit items (try to get gender-specific, fallback to general)
        outfit_items = _extract_outfit_items(response, gen, season)
        
        # Generate style notes (combine LLM insights with weather-based notes)
        style_notes = _generate_style_notes(weather_data, high_f, low_f, rain_chance)
        # Try to extract additional style notes from LLM response
        llm_style_hints = _extract_style_notes_from_llm(response)
        if llm_style_hints:
            style_notes = f"{style_notes}. {llm_style_hints}" if style_notes else llm_style_hints
        
        suggestions[gen] = {
            "outfit_items": outfit_items,
            "color_palette": colors[:6],  # Limit to 6 colors
            "style_notes": style_notes,
            "special_items": _get_special_items(rain_chance, high_f, low_f)
        }
    
    return suggestions


def _extract_style_notes_from_llm(response: str) -> str:
    """Extract style notes or fashion advice from LLM response."""
    # Look for common fashion advice phrases
    style_keywords = [
        "layering", "versatile", "mix and match", "coordinate", "complement",
        "comfortable", "stylish", "modern", "classic", "trendy", "elegant"
    ]
    
    sentences = response.split('.')
    style_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in style_keywords):
            # Clean up the sentence
            cleaned = sentence.strip()
            if len(cleaned) > 20:  # Only include substantial sentences
                style_sentences.append(cleaned)
    
    if style_sentences:
        return ". ".join(style_sentences[:2])  # Return up to 2 relevant sentences
    
    return ""


def _extract_colors(response: str, season: Optional[str] = None) -> List[Dict[str, str]]:
    """Extract color palette from LLM response."""
    colors = []
    
    # Extended color names and their hex codes (trendy colors)
    color_map = {
        "navy": "#1a1a2e", "blue": "#3498db", "sky blue": "#87ceeb", "ocean blue": "#006994",
        "black": "#000000", "white": "#ffffff", "gray": "#808080", "grey": "#808080", "charcoal": "#36454f", "slate gray": "#708090",
        "beige": "#f5f5dc", "tan": "#d2b48c", "khaki": "#c3b091", "cream": "#fffdd0", "camel": "#c19a6b",
        "olive": "#808000", "green": "#2ecc71", "forest green": "#228b22", "sage green": "#9caf88",
        "burgundy": "#800020", "maroon": "#800000", "red": "#e74c3c", "rust": "#b7410e",
        "coral": "#ff7f50", "peach": "#ffdab9", "pink": "#ffc0cb", "blush pink": "#ffb6c1",
        "purple": "#9b59b6", "lavender": "#e6e6fa",
        "yellow": "#f1c40f", "mustard": "#ffdb58", "butter yellow": "#fffacd",
        "orange": "#ff9800", "terracotta": "#e07a5f", "sunset orange": "#ff6347",
        "brown": "#8b4513", "chocolate": "#7b3f00",
        "turquoise": "#40e0d0"
    }
    
    response_lower = response.lower()
    
    # Look for color mentions (prioritize longer color names first)
    sorted_colors = sorted(color_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for color_name, hex_code in sorted_colors:
        if color_name in response_lower:
            # Check if we already have this color (case-insensitive)
            if not any(c["name"].lower() == color_name.lower() for c in colors):
                colors.append({
                    "name": color_name.title(),
                    "hex": hex_code
                })
    
    return colors


def _get_default_colors_for_weather(response: str, season: Optional[str] = None) -> List[Dict[str, str]]:
    """Get trendy default color palette based on weather keywords and season."""
    response_lower = response.lower()
    
    # Season-based trendy color palettes
    if season == "winter":
        return [
            {"name": "Charcoal", "hex": "#36454f"},
            {"name": "Burgundy", "hex": "#800020"},
            {"name": "Camel", "hex": "#c19a6b"},
            {"name": "Cream", "hex": "#fffdd0"},
            {"name": "Forest Green", "hex": "#228b22"}
        ]
    elif season == "spring":
        return [
            {"name": "Sage Green", "hex": "#9caf88"},
            {"name": "Lavender", "hex": "#e6e6fa"},
            {"name": "Blush Pink", "hex": "#ffb6c1"},
            {"name": "Butter Yellow", "hex": "#fffacd"},
            {"name": "Sky Blue", "hex": "#87ceeb"}
        ]
    elif season == "summer":
        return [
            {"name": "Turquoise", "hex": "#40e0d0"},
            {"name": "Coral", "hex": "#ff7f50"},
            {"name": "White", "hex": "#ffffff"},
            {"name": "Sunset Orange", "hex": "#ff6347"},
            {"name": "Ocean Blue", "hex": "#006994"}
        ]
    elif season == "fall":
        return [
            {"name": "Terracotta", "hex": "#e07a5f"},
            {"name": "Mustard", "hex": "#ffdb58"},
            {"name": "Olive", "hex": "#808000"},
            {"name": "Rust", "hex": "#b7410e"},
            {"name": "Cream", "hex": "#fffdd0"}
        ]
    
    # Weather-based fallbacks
    if "rain" in response_lower or "wet" in response_lower:
        return [
            {"name": "Navy", "hex": "#1a1a2e"},
            {"name": "Slate Gray", "hex": "#708090"},
            {"name": "Charcoal", "hex": "#36454f"},
            {"name": "White", "hex": "#ffffff"}
        ]
    elif "sun" in response_lower or "warm" in response_lower:
        return [
            {"name": "Sky Blue", "hex": "#87ceeb"},
            {"name": "White", "hex": "#ffffff"},
            {"name": "Beige", "hex": "#f5f5dc"},
            {"name": "Coral", "hex": "#ff7f50"}
        ]
    elif "cold" in response_lower or "winter" in response_lower:
        return [
            {"name": "Navy", "hex": "#1a1a2e"},
            {"name": "Burgundy", "hex": "#800020"},
            {"name": "Gray", "hex": "#808080"},
            {"name": "Camel", "hex": "#c19a6b"}
        ]
    else:
        # Trendy neutral palette
        return [
            {"name": "Navy", "hex": "#1a1a2e"},
            {"name": "Beige", "hex": "#f5f5dc"},
            {"name": "White", "hex": "#ffffff"},
            {"name": "Olive", "hex": "#808000"},
            {"name": "Terracotta", "hex": "#e07a5f"}
        ]


def _extract_outfit_items(response: str, gender: str, season: Optional[str] = None) -> Dict[str, List[str]]:
    """Extract outfit items from LLM response."""
    items = {
        "tops": [],
        "bottoms": [],
        "outerwear": [],
        "footwear": [],
        "accessories": []
    }
    
    response_lower = response.lower()
    
    # Enhanced keyword-based extraction with trendy items
    if "t-shirt" in response_lower or "tee" in response_lower:
        items["tops"].append("T-shirts")
    if "blouse" in response_lower:
        items["tops"].append("Blouses")
    if "sweater" in response_lower or "pullover" in response_lower or "knit" in response_lower:
        items["tops"].append("Sweaters")
    if "shirt" in response_lower and "t-shirt" not in response_lower:
        items["tops"].append("Shirts")
    if "tank" in response_lower:
        items["tops"].append("Tank tops")
    if "turtleneck" in response_lower:
        items["tops"].append("Turtlenecks")
    if "hoodie" in response_lower:
        items["tops"].append("Hoodies")
    
    if "jeans" in response_lower:
        items["bottoms"].append("Jeans")
    if "pants" in response_lower and "jeans" not in response_lower:
        items["bottoms"].append("Pants")
    if "shorts" in response_lower:
        items["bottoms"].append("Shorts")
    if "skirt" in response_lower:
        items["bottoms"].append("Skirts")
    if "dress" in response_lower:
        items["bottoms"].append("Dresses")
    if "chinos" in response_lower:
        items["bottoms"].append("Chinos")
    
    if "jacket" in response_lower:
        items["outerwear"].append("Jacket")
    if "coat" in response_lower:
        items["outerwear"].append("Coat")
    if "cardigan" in response_lower:
        items["outerwear"].append("Cardigan")
    if "bomber" in response_lower:
        items["outerwear"].append("Bomber jacket")
    if "denim" in response_lower and "jacket" in response_lower:
        items["outerwear"].append("Denim jacket")
    if "trench" in response_lower:
        items["outerwear"].append("Trench coat")
    
    if "sneakers" in response_lower or "sneaker" in response_lower:
        items["footwear"].append("Sneakers")
    if "boots" in response_lower or "boot" in response_lower:
        items["footwear"].append("Boots")
    if "sandals" in response_lower:
        items["footwear"].append("Sandals")
    if "flats" in response_lower:
        items["footwear"].append("Flats")
    if "loafers" in response_lower:
        items["footwear"].append("Loafers")
    
    if "umbrella" in response_lower:
        items["accessories"].append("Umbrella")
    if "hat" in response_lower or "cap" in response_lower:
        items["accessories"].append("Hat")
    if "sunglasses" in response_lower:
        items["accessories"].append("Sunglasses")
    if "bag" in response_lower or "purse" in response_lower:
        items["accessories"].append("Bag")
    if "watch" in response_lower:
        items["accessories"].append("Watch")
    if "scarf" in response_lower:
        items["accessories"].append("Scarf")
    
    # If no items extracted, use trendy fallback
    if not any(items.values()):
        items = _get_fallback_outfit_items(gender, season)
    
    return items


def _get_fallback_outfit_items(gender: str, season: Optional[str] = None) -> Dict[str, List[str]]:
    """Get trendy fallback outfit items based on gender and season."""
    base_items = {
        "female": {
            "spring": {
                "tops": ["Trendy blouses", "Lightweight sweaters", "Tank tops"],
                "bottoms": ["High-waisted jeans", "Midi skirts", "Wide-leg pants"],
                "outerwear": ["Denim jacket", "Trench coat", "Cardigan"],
                "footwear": ["Ankle boots", "Sneakers", "Flats"],
                "accessories": ["Crossbody bag", "Scarf", "Sunglasses", "Hair accessories"]
            },
            "summer": {
                "tops": ["Off-shoulder tops", "Linen shirts", "Crop tops"],
                "bottoms": ["Shorts", "Midi dresses", "Wide-leg linen pants"],
                "outerwear": ["Light kimono", "Denim jacket"],
                "footwear": ["Sandals", "Espadrilles", "Sneakers"],
                "accessories": ["Straw hat", "Sunglasses", "Tote bag", "Statement jewelry"]
            },
            "fall": {
                "tops": ["Knitted sweaters", "Turtlenecks", "Blouses"],
                "bottoms": ["Jeans", "Midi skirts", "Corduroy pants"],
                "outerwear": ["Leather jacket", "Trench coat", "Cardigan"],
                "footwear": ["Ankle boots", "Loafers", "Sneakers"],
                "accessories": ["Scarf", "Crossbody bag", "Beret", "Layered necklaces"]
            },
            "winter": {
                "tops": ["Wool sweaters", "Turtlenecks", "Thermal layers"],
                "bottoms": ["Jeans", "Wool pants", "Leggings"],
                "outerwear": ["Wool coat", "Puffer jacket", "Trench coat"],
                "footwear": ["Boots", "Ankle boots", "Sneakers"],
                "accessories": ["Scarf", "Beanie", "Gloves", "Crossbody bag"]
            }
        },
        "male": {
            "spring": {
                "tops": ["Button-down shirts", "Polo shirts", "Light sweaters"],
                "bottoms": ["Chinos", "Jeans", "Cargo pants"],
                "outerwear": ["Denim jacket", "Light bomber", "Cardigan"],
                "footwear": ["Sneakers", "Loafers", "Chelsea boots"],
                "accessories": ["Watch", "Sunglasses", "Baseball cap", "Backpack"]
            },
            "summer": {
                "tops": ["T-shirts", "Polo shirts", "Linen shirts"],
                "bottoms": ["Shorts", "Chinos", "Light jeans"],
                "outerwear": ["Light jacket", "Overshirt"],
                "footwear": ["Sneakers", "Sandals", "Loafers"],
                "accessories": ["Sunglasses", "Baseball cap", "Watch", "Weekender bag"]
            },
            "fall": {
                "tops": ["Flannel shirts", "Hoodies", "Sweaters"],
                "bottoms": ["Jeans", "Chinos", "Cargo pants"],
                "outerwear": ["Denim jacket", "Bomber jacket", "Cardigan"],
                "footwear": ["Sneakers", "Boots", "Chelsea boots"],
                "accessories": ["Watch", "Beanie", "Backpack", "Scarf"]
            },
            "winter": {
                "tops": ["Wool sweaters", "Hoodies", "Flannel shirts"],
                "bottoms": ["Jeans", "Wool pants", "Cargo pants"],
                "outerwear": ["Wool coat", "Puffer jacket", "Parka"],
                "footwear": ["Boots", "Sneakers", "Chelsea boots"],
                "accessories": ["Beanie", "Gloves", "Scarf", "Watch"]
            }
        }
    }
    
    gender_key = "female" if gender.lower() == "female" else "male"
    season_key = season if season and season in ["spring", "summer", "fall", "winter"] else "spring"
    
    return base_items.get(gender_key, {}).get(season_key, {
        "tops": ["T-shirts", "Shirts"],
        "bottoms": ["Jeans", "Pants"],
        "outerwear": ["Jacket"],
        "footwear": ["Sneakers"],
        "accessories": ["Watch"]
    })


def _generate_style_notes(weather_data: Dict[str, Any], high_f: float, low_f: float, rain_chance: float) -> str:
    """Generate style notes based on weather."""
    notes = []
    
    if rain_chance > 0.5:
        notes.append("Pack waterproof or water-resistant items due to high rain chance")
    
    if high_f - low_f > 20:
        notes.append("Layering is key due to significant temperature variation between day and night")
    elif high_f > 80:
        notes.append("Lightweight, breathable fabrics are recommended for warm weather")
    elif low_f < 50:
        notes.append("Pack warmer layers for cooler temperatures")
    
    if weather_data.get("summary", "").lower() in ["sunny", "clear"]:
        notes.append("Bright colors and sun protection are recommended")
    
    return ". ".join(notes) if notes else "Pack versatile pieces that can be mixed and matched"


def _get_special_items(rain_chance: float, high_f: float, low_f: float) -> List[str]:
    """Get special items needed based on weather."""
    items = []
    
    if rain_chance > 0.5:
        items.append("Umbrella")
        items.append("Waterproof jacket or raincoat")
    
    if high_f > 75:
        items.append("Sunglasses")
        items.append("Sun hat or cap")
        items.append("Sunscreen")
    
    if low_f < 45:
        items.append("Warm hat")
        items.append("Gloves")
        items.append("Scarf")
    
    return items


def _get_fallback_for_gender(
    gender: str,
    weather_data: Dict[str, Any],
    high_f: float,
    low_f: float,
    rain_chance: float,
    season: Optional[str] = None
) -> Dict[str, Any]:
    """Get trendy fallback clothing suggestions for a specific gender."""
    outfit_items = _get_fallback_outfit_items(gender, season)
    colors = _get_default_colors_for_weather("", season)
    style_notes = _generate_style_notes(weather_data, high_f, low_f, rain_chance)
    
    # Enhance style notes with season-specific trendy advice
    if season:
        season_notes = {
            "spring": "Spring calls for lighter layers and fresh, vibrant colors. Mix textures like linen and cotton for a modern look.",
            "summer": "Summer style is all about breathable fabrics and light colors. Embrace flowy silhouettes and sun protection.",
            "fall": "Fall fashion focuses on rich colors and cozy layers. Mix textures like wool, denim, and corduroy for depth.",
            "winter": "Winter style combines warmth with sophistication. Layer with purpose and incorporate rich, deep colors."
        }
        if season_notes.get(season):
            style_notes = f"{style_notes}. {season_notes[season]}" if style_notes else season_notes[season]
    
    special_items = _get_special_items(rain_chance, high_f, low_f)
    
    return {
        "outfit_items": outfit_items,
        "color_palette": colors,
        "style_notes": style_notes,
        "special_items": special_items
    }


def _get_fallback_suggestions(
    weather_data: Dict[str, Any],
    gender: str,
    high_f: float,
    low_f: float,
    rain_chance: float,
    season: Optional[str] = None,
    destination: str = ""
) -> Dict[str, Any]:
    """Get trendy fallback clothing suggestions when LLM fails."""
    summary = weather_data.get("summary", "Pleasant") if isinstance(weather_data, dict) else "Pleasant"
    climate_zone = get_destination_climate_zone(destination) if destination else "moderate"
    
    genders_to_process = ["male", "female"] if gender == "both" else [gender]
    suggestions = {}
    
    for gen in genders_to_process:
        suggestions[gen] = _get_fallback_for_gender(gen, weather_data if isinstance(weather_data, dict) else {}, high_f, low_f, rain_chance, season)
    
    return {
        "status": "success",
        "weather_summary": summary,
        "temperature_range": f"{low_f}°F - {high_f}°F",
        "rain_chance": rain_chance,
        "season": season,
        "seasons": [season] if season else [],
        "climate_zone": climate_zone,
        "weather_source": "fallback",
        "suggestions": suggestions,
        "raw_llm_response": f"Trendy fallback suggestions based on {season} season and {climate_zone} climate" if season else f"Trendy fallback suggestions based on {climate_zone} climate"
    }

