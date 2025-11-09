"""
Synthesizer module for creating final itinerary with budget breakdown and map points.
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from .state import (
    AgentState, Itinerary, ItineraryItem, BudgetBreakdown, MapPoint,
    ClothingRecommendations, ClothingSuggestion, OutfitItems, ColorPalette,
    MusicRecommendations, SongRecommendation, CityHistory
)
from tools import clothing, music, history

logger = logging.getLogger(__name__)


def create_itinerary(agent_state: AgentState, user_request) -> Itinerary:
    """
    Create a complete itinerary with schedule, budget breakdown, and map points.
    """
    logger.info("Creating final itinerary from agent selections")
    
    # Create itinerary items (daily schedule)
    itinerary_items = _create_daily_schedule(agent_state, user_request)
    
    # Create budget breakdown
    budget_breakdown = _create_budget_breakdown(agent_state, user_request.budget_total)
    
    # Create map points for visualization
    map_points = _create_map_points(agent_state)
    
    # Extract decision rationales from agent log
    rationales = _extract_rationales(agent_state)
    
    # Extract key agent decisions
    agent_decisions = _extract_agent_decisions(agent_state)
    
    # Generate clothing recommendations based on weather
    clothing_recommendations = _generate_clothing_recommendations(agent_state, user_request)
    
    # Generate music recommendations based on location
    music_recommendations = _generate_music_recommendations(agent_state, user_request)
    
    # Generate city history using Gemini API
    city_history = _generate_city_history(user_request)
    
    itinerary = Itinerary(
        items=itinerary_items,
        budget_breakdown=budget_breakdown,
        map_points=map_points,
        rationales=rationales,
        agent_decisions=agent_decisions,
        clothing_recommendations=clothing_recommendations,
        music_recommendations=music_recommendations,
        city_history=city_history
    )
    
    logger.info(f"Created itinerary with {len(itinerary_items)} items and {len(map_points)} map points")
    
    return itinerary


def _create_daily_schedule(agent_state: AgentState, user_request) -> List[ItineraryItem]:
    """Create a day-by-day schedule with time blocks."""
    
    items = []
    current_date = user_request.start_date
    end_date = user_request.end_date
    
    # Time blocks for each day
    time_blocks = [
        ("Morning", "9:00 AM - 12:00 PM"),
        ("Afternoon", "1:00 PM - 4:00 PM"), 
        ("Evening", "6:00 PM - 9:00 PM")
    ]
    
    activities = agent_state.selections.activities.copy()
    activity_index = 0
    
    # Iterate through all dates regardless of activities to ensure schedule is created
    while current_date <= end_date:
        
        # First day: Add arrival/transport
        if current_date == user_request.start_date:
            # Create transport item with appropriate description
            if agent_state.selections.transport:
                if agent_state.selections.transport.mode == "flying":
                    transport_title = f"Fly from {user_request.origin} to {user_request.destination}"
                    transport_notes = f"Flight time: ~{agent_state.selections.transport.duration_minutes//60}h {agent_state.selections.transport.duration_minutes%60}m (including airport time)"
                else:
                    transport_title = f"Travel from {user_request.origin}"
                    transport_notes = f"Driving time: {agent_state.selections.transport.duration_minutes} minutes"
            else:
                transport_title = f"Travel from {user_request.origin}"
                transport_notes = ""
            
            transport_item = ItineraryItem(
                day=current_date,
                time="Arrival",
                title=transport_title,
                est_cost=agent_state.selections.transport.cost if agent_state.selections.transport else 0.0,
                notes=transport_notes
            )
            items.append(transport_item)
            
            # Add hotel check-in
            if agent_state.selections.hotel:
                checkin_item = ItineraryItem(
                    day=current_date,
                    time="Check-in",
                    title=f"Check into {agent_state.selections.hotel.name}",
                    address=agent_state.selections.hotel.address,
                    link=agent_state.selections.hotel.link,
                    est_cost=0.0,
                    notes=f"Hotel for ${agent_state.selections.hotel.price_per_night}/night"
                )
                items.append(checkin_item)
        
        # Add activities for the day (up to 3 per day) if available
        daily_activities = 0
        for time_slot in time_blocks:
            if activity_index < len(activities) and daily_activities < 3:
                activity = activities[activity_index]
                
                # Calculate cost: price per person * number of travelers
                # For itinerary display, show cost per person (price), but budget uses total
                activity_cost_per_person = activity.price if activity.price > 0 else 0.0
                
                activity_item = ItineraryItem(
                    day=current_date,
                    time=time_slot[1],
                    title=activity.name,
                    place_id=activity.place_id,
                    address=activity.address,
                    link=activity.link,
                    est_cost=activity_cost_per_person,  # Show per-person cost in itinerary
                    notes=f"Rating: {activity.rating}/5, Tags: {', '.join(activity.tags[:3])}" + 
                          (f", Price: ${activity_cost_per_person:.2f}/person" if activity_cost_per_person > 0 else ", Free")
                )
                items.append(activity_item)
                
                activity_index += 1
                daily_activities += 1
        
        # Add free time slots if no activities for this day
        if daily_activities == 0 and current_date != user_request.start_date and current_date != end_date:
            # Add a free time suggestion for days without activities
            free_time_item = ItineraryItem(
                day=current_date,
                time="Flexible",
                title="Free time to explore",
                est_cost=0.0,
                notes="Explore the destination at your own pace"
            )
            items.append(free_time_item)
        
        # Last day: Add departure
        if current_date == end_date:
            if agent_state.selections.hotel:
                checkout_item = ItineraryItem(
                    day=current_date,
                    time="Check-out",
                    title=f"Check out of {agent_state.selections.hotel.name}",
                    est_cost=0.0,
                    notes="End of stay"
                )
                items.append(checkout_item)
            
            departure_item = ItineraryItem(
                day=current_date,
                time="Departure",
                title=f"Return to {user_request.origin}",
                est_cost=0.0,
                notes="Safe travels!"
            )
            items.append(departure_item)
        
        current_date += timedelta(days=1)
    
    # Add any remaining activities to the last day
    while activity_index < len(activities):
        activity = activities[activity_index]
        
        extra_item = ItineraryItem(
            day=end_date,
            time="Flexible",
            title=activity.name,
            place_id=activity.place_id,
            address=activity.address,
            link=activity.link,
            est_cost=activity.price,
            notes=f"Backup activity - {', '.join(activity.tags[:2])}"
        )
        items.append(extra_item)
        activity_index += 1
    
    return items


def _create_budget_breakdown(agent_state: AgentState, total_budget: float) -> BudgetBreakdown:
    """Create detailed budget breakdown by category."""
    
    transport_cost = 0.0
    if agent_state.selections.transport:
        transport_cost = agent_state.selections.transport.cost
    
    lodging_cost = 0.0
    if agent_state.selections.hotel:
        lodging_cost = agent_state.selections.hotel.total_price
    
    activities_cost = 0.0
    if agent_state.selections.activities and len(agent_state.selections.activities) > 0:
        # Calculate activities cost: price per person * number of travelers (assume 2 for now)
        # Sum all activity prices and multiply by 2 (for 2 travelers)
        # Free activities (price = 0.0) contribute $0 to the total, but are still counted
        num_travelers = 2  # TODO: Get from user_request.travelers
        
        # Log detailed breakdown before calculation
        activity_details = []
        for activity in agent_state.selections.activities:
            activity_total = activity.price * num_travelers
            activities_cost += activity_total
            activity_details.append(f"  - {activity.name}: ${activity.price:.2f}/person × {num_travelers} = ${activity_total:.2f}")
        
        logger.info(f"📊 Activities Budget Calculation:")
        logger.info(f"   Number of activities: {len(agent_state.selections.activities)}")
        logger.info(f"   Number of travelers: {num_travelers}")
        for detail in activity_details:
            logger.info(detail)
        logger.info(f"   Total activities cost: ${activities_cost:.2f}")
        
        # Validate that we have a non-zero cost if we have paid activities
        paid_activities = [a for a in agent_state.selections.activities if a.price > 0]
        if len(paid_activities) > 0 and activities_cost == 0.0:
            logger.error(f"⚠️ WARNING: Found {len(paid_activities)} paid activities but total cost is $0.0!")
            logger.error(f"   Paid activities: {[a.name for a in paid_activities]}")
            logger.error(f"   Activity prices: {[a.price for a in paid_activities]}")
    else:
        logger.warning("⚠️ No activities found in agent_state.selections.activities - activities cost will be $0")
        if agent_state.selections.activities is not None:
            logger.warning(f"   activities list exists but is empty: {agent_state.selections.activities}")
    
    total_spent = transport_cost + lodging_cost + activities_cost
    remaining = total_budget - total_spent
    
    logger.info(f"Budget breakdown: Transport=${transport_cost:.2f}, Lodging=${lodging_cost:.2f}, Activities=${activities_cost:.2f}, Total=${total_spent:.2f}, Remaining=${remaining:.2f}")
    
    return BudgetBreakdown(
        transport=transport_cost,
        lodging=lodging_cost,
        activities=activities_cost,
        total_spent=total_spent,
        remaining=remaining
    )


def _create_map_points(agent_state: AgentState) -> List[MapPoint]:
    """Create map points for hotel and activities."""
    
    map_points = []
    
    # Add hotel point
    if agent_state.selections.hotel:
        hotel_point = MapPoint(
            name=agent_state.selections.hotel.name,
            lat=agent_state.selections.hotel.lat,
            lng=agent_state.selections.hotel.lng,
            link=agent_state.selections.hotel.link,
            type="hotel"
        )
        map_points.append(hotel_point)
    
    # Add activity points
    for activity in agent_state.selections.activities:
        activity_point = MapPoint(
            name=activity.name,
            lat=activity.lat,
            lng=activity.lng,
            link=activity.link,
            type="activity"
        )
        map_points.append(activity_point)
    
    return map_points


def _extract_rationales(agent_state: AgentState) -> List[str]:
    """Extract decision rationales from agent log."""
    
    rationales = []
    
    for tool_result in agent_state.log:
        if tool_result.notes and "selected" in tool_result.notes.lower():
            rationales.append(f"{tool_result.tool}: {tool_result.notes}")
    
    # Add budget rationale
    if agent_state.selections.hotel:
        budget_remaining = agent_state.budget_remaining
        if budget_remaining > 200:
            rationales.append("Budget management: Comfortable buffer remaining for unexpected expenses")
        elif budget_remaining > 50:
            rationales.append("Budget management: Good balance between selections and remaining budget")
        else:
            rationales.append("Budget management: Maximized budget utilization with minimal buffer")
    
    return rationales


def _extract_agent_decisions(agent_state: AgentState) -> List[str]:
    """Extract key agent decisions and re-planning moments."""
    
    decisions = []
    
    # Check for Plan B hotel decision
    plan_b_found = any("plan_b" in result.notes.lower() for result in agent_state.log)
    if plan_b_found:
        decisions.append("🏨 Triggered hotel Plan B due to budget constraints - selected more affordable option")
    
    # Check for weather re-planning
    weather_replan = any("weather re-plan" in result.notes.lower() for result in agent_state.log)
    if weather_replan:
        decisions.append("🌧️ Adjusted activity selection for rainy weather - prioritized indoor venues")
    
    # Check for multi-interest matches
    multi_interest = any("multi-interest" in result.notes.lower() for result in agent_state.log)
    if multi_interest:
        decisions.append("🎯 Found venues matching multiple interests - optimized for user preferences")
    
    # Check for location optimization
    location_filter = any("distance" in result.notes.lower() or "nearby" in result.notes.lower() for result in agent_state.log)
    if location_filter:
        decisions.append("📍 Filtered activities by proximity to hotel - minimized travel time")
    
    # Budget optimization decision
    final_budget = agent_state.budget_remaining
    total_selections = len([s for s in [agent_state.selections.transport, agent_state.selections.hotel] if s]) + len(agent_state.selections.activities)
    
    if total_selections > 0:
        decisions.append(f"💰 Optimized {total_selections} selections within ${agent_state.budget_remaining + sum(result.cost_estimate for result in agent_state.log):.0f} budget")
    
    # Transport decision
    if agent_state.selections.transport:
        if agent_state.selections.transport.mode == "flying":
            decisions.append(f"✈️ Selected flying for {agent_state.selections.transport.distance_miles:.0f} mile trip - faster travel for long distance")
        else:
            decisions.append(f"🚗 Selected driving for {agent_state.selections.transport.distance_miles:.0f} mile trip - cost-effective for shorter distances")
    
    return decisions


def generate_calendar_events(itinerary: Itinerary) -> List[Dict[str, Any]]:
    """Generate calendar events in ICS format data."""
    
    events = []
    
    for item in itinerary.items:
        # Skip non-activity items
        if item.time in ["Arrival", "Check-in", "Check-out", "Departure"]:
            continue
        
        # Parse time range if available
        start_time = "09:00"
        end_time = "10:00"
        
        if "9:00 AM - 12:00 PM" in item.time:
            start_time = "09:00"
            end_time = "12:00"
        elif "1:00 PM - 4:00 PM" in item.time:
            start_time = "13:00"
            end_time = "16:00"
        elif "6:00 PM - 9:00 PM" in item.time:
            start_time = "18:00"
            end_time = "21:00"
        
        event = {
            "summary": item.title,
            "start": f"{item.day.isoformat()}T{start_time}:00",
            "end": f"{item.day.isoformat()}T{end_time}:00",
            "location": item.address or "",
            "description": f"{item.notes or ''}\nCost: ${item.est_cost:.2f}",
            "url": item.link or ""
        }
        
        events.append(event)
    
    return events


def _generate_clothing_recommendations(agent_state: AgentState, user_request) -> Optional[ClothingRecommendations]:
    """Generate clothing recommendations based on weather data and/or season."""
    
    # Find weather data from agent log (optional - we can use season if not available)
    weather_data = None
    for tool_result in agent_state.log:
        if tool_result.tool == "weather.forecast":
            weather_data = tool_result.output
            break
    
    try:
        # Calculate number of days
        days = (user_request.end_date - user_request.start_date).days + 1
        
        # Generate clothing suggestions for both genders
        # Always generate - uses season if weather API not available
        clothing_result = clothing.suggest_clothing(
            weather_data=weather_data,  # Can be None - will use season
            gender="both",
            destination=user_request.destination,
            days=days,
            start_date=user_request.start_date,
            end_date=user_request.end_date
        )
        
        if clothing_result.get("status") != "success":
            return None
        
        suggestions_data = clothing_result.get("suggestions", {})
        
        # Convert to Pydantic models
        male_suggestions = None
        female_suggestions = None
        
        if "male" in suggestions_data:
            male_data = suggestions_data["male"]
            male_suggestions = ClothingSuggestion(
                outfit_items=OutfitItems(
                    tops=male_data.get("outfit_items", {}).get("tops", []),
                    bottoms=male_data.get("outfit_items", {}).get("bottoms", []),
                    outerwear=male_data.get("outfit_items", {}).get("outerwear", []),
                    footwear=male_data.get("outfit_items", {}).get("footwear", []),
                    accessories=male_data.get("outfit_items", {}).get("accessories", [])
                ),
                color_palette=[
                    ColorPalette(name=c["name"], hex=c["hex"])
                    for c in male_data.get("color_palette", [])
                ],
                style_notes=male_data.get("style_notes", ""),
                special_items=male_data.get("special_items", [])
            )
        
        if "female" in suggestions_data:
            female_data = suggestions_data["female"]
            female_suggestions = ClothingSuggestion(
                outfit_items=OutfitItems(
                    tops=female_data.get("outfit_items", {}).get("tops", []),
                    bottoms=female_data.get("outfit_items", {}).get("bottoms", []),
                    outerwear=female_data.get("outfit_items", {}).get("outerwear", []),
                    footwear=female_data.get("outfit_items", {}).get("footwear", []),
                    accessories=female_data.get("outfit_items", {}).get("accessories", [])
                ),
                color_palette=[
                    ColorPalette(name=c["name"], hex=c["hex"])
                    for c in female_data.get("color_palette", [])
                ],
                style_notes=female_data.get("style_notes", ""),
                special_items=female_data.get("special_items", [])
            )
        
        return ClothingRecommendations(
            weather_summary=clothing_result.get("weather_summary", ""),
            temperature_range=clothing_result.get("temperature_range", ""),
            rain_chance=clothing_result.get("rain_chance", 0.0),
            season=clothing_result.get("season"),
            seasons=clothing_result.get("seasons", []),
            climate_zone=clothing_result.get("climate_zone"),
            weather_source=clothing_result.get("weather_source"),
            male_suggestions=male_suggestions,
            female_suggestions=female_suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to generate clothing recommendations: {e}")
        return None


def _generate_music_recommendations(agent_state: AgentState, user_request) -> Optional[MusicRecommendations]:
    """Generate music recommendations based on destination location."""
    
    try:
        # Get season and climate zone from clothing recommendations if available
        season = None
        climate_zone = None
        
        # Try to get from clothing recommendations first
        for tool_result in agent_state.log:
            if tool_result.tool == "weather.forecast":
                # We can infer season from dates
                season = _get_season_from_dates(user_request.start_date)
                break
        
        # Get climate zone from destination
        from tools.clothing import get_destination_climate_zone
        climate_zone = get_destination_climate_zone(user_request.destination)
        
        # Generate music recommendations
        music_result = music.recommend_music(
            destination=user_request.destination,
            season=season,
            climate_zone=climate_zone,
            mood="vibrant"
        )
        
        if music_result.get("status") != "success":
            return None
        
        # Convert to Pydantic models with cleaned names
        from tools.music import _clean_song_name, _clean_artist_name
        
        song_recommendations = []
        for song_data in music_result.get("recommendations", [])[:12]:  # Limit to 12 songs
            # Clean song title and artist name
            title = _clean_song_name(song_data.get("title", "Unknown"))
            artist = _clean_artist_name(song_data.get("artist", "Unknown Artist"))
            genre = song_data.get("genre", "Pop").strip().title()
            mood = song_data.get("mood", "Upbeat").strip().title()
            
            song_rec = SongRecommendation(
                title=title,
                artist=artist,
                genre=genre,
                mood=mood,
                why=song_data.get("why", f"Perfect for {user_request.destination}").strip(),
                best_for=song_data.get("best_for", "Social Media Posts").strip()
            )
            song_recommendations.append(song_rec)
        
        if not song_recommendations:
            return None
        
        return MusicRecommendations(
            destination=user_request.destination,
            location_genres=music_result.get("location_genres", []),
            season=season,
            mood=music_result.get("mood", "vibrant"),
            songs=song_recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to generate music recommendations: {e}")
        return None


def _get_season_from_dates(start_date: date) -> Optional[str]:
    """Get season from start date."""
    month = start_date.month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"


def create_summary_statistics(itinerary: Itinerary) -> Dict[str, Any]:
    """Create summary statistics for the itinerary."""
    
    stats = {
        "total_activities": len([item for item in itinerary.items if item.time not in ["Arrival", "Check-in", "Check-out", "Departure"]]),
        "total_days": len(set(item.day for item in itinerary.items)),
        "budget_utilization": (itinerary.budget_breakdown.total_spent / (itinerary.budget_breakdown.total_spent + itinerary.budget_breakdown.remaining)) * 100,
        "avg_activity_cost": itinerary.budget_breakdown.activities / max(1, len(itinerary.items)) if itinerary.budget_breakdown.activities > 0 else 0,
        "map_coverage": len(itinerary.map_points),
        "decision_points": len(itinerary.agent_decisions)
    }
    
    return stats


def _generate_city_history(user_request) -> Optional[CityHistory]:
    """Generate city history using Gemini API."""
    
    try:
        destination = user_request.destination
        logger.info(f"Generating city history for {destination} using Gemini API")
        
        # Call history tool
        history_result = history.generate_city_history(destination, max_length=500)
        
        if history_result.get("status") == "success":
            return CityHistory(
                destination=history_result.get("destination", destination),
                history=history_result.get("history", ""),
                source=history_result.get("source", "gemini_api"),
                length=history_result.get("length", 0)
            )
        else:
            logger.warning(f"Failed to generate city history: {history_result}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to generate city history: {e}")
        return None
