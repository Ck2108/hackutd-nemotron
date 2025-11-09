"""
Executor module for running plan steps, updating budget, and handling re-planning.
"""
import logging
from datetime import date, datetime
from typing import Dict, Any, List
from .state import AgentState, ToolResult, TransportSelection, HotelSelection, ActivitySelection
from .planner import update_plan_with_constraints
from tools import maps, weather, places, hotels

logger = logging.getLogger(__name__)


def execute_plan(agent_state: AgentState) -> AgentState:
    """
    Execute all steps in the agent's plan, updating budget and handling re-planning.
    """
    logger.info(f"Executing plan with {len(agent_state.plan)} steps")
    
    for i, step in enumerate(agent_state.plan):
        logger.info(f"Executing step {i+1}/{len(agent_state.plan)}: {step.description}")
        
        try:
            # Execute the tool call
            result = _execute_tool_call(step.tool, step.params)
            
            # Create tool result log entry
            tool_result = ToolResult(
                tool=step.tool,
                input=step.params,
                output=result,
                cost_estimate=0.0,  # Will be updated based on tool type
                notes="",
                thinking=""  # Will be populated by thinking logic
            )
            
            # Process result based on tool type and update state
            agent_state = _process_tool_result(agent_state, step, tool_result)
            
            # Add to log
            agent_state.log.append(tool_result)
            
            # Check for constraint violations and re-plan if needed
            agent_state = _check_constraints_and_replan(agent_state, step, result)
            
        except Exception as e:
            logger.error(f"Failed to execute step {step.description}: {e}")
            
            # Add error to log
            error_result = ToolResult(
                tool=step.tool,
                input=step.params,
                output={"error": str(e)},
                cost_estimate=0.0,
                notes=f"Tool execution failed: {e}"
            )
            agent_state.log.append(error_result)
    
    logger.info(f"Plan execution completed. Budget remaining: ${agent_state.budget_remaining:.2f}")
    return agent_state


def _execute_tool_call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific tool call and return the result."""
    
    if tool_name == "maps.find_directions":
        return maps.find_directions(params["origin"], params["destination"])
    
    elif tool_name == "weather.forecast":
        start_date = None
        end_date = None
        
        if "start_date" in params:
            start_date = datetime.fromisoformat(params["start_date"]).date()
        if "end_date" in params:
            end_date = datetime.fromisoformat(params["end_date"]).date()
        
        return weather.forecast(params["city"], start_date, end_date)
    
    elif tool_name == "places.search":
        return {
            "places": places.search(
                params["query"], 
                params["near"], 
                params.get("limit", 10)
            )
        }
    
    elif tool_name == "hotels.search":
        # Handle both string and date objects
        if isinstance(params.get("start_date"), str):
            start_date = datetime.fromisoformat(params["start_date"]).date()
        else:
            start_date = params.get("start_date")
        
        if isinstance(params.get("end_date"), str):
            end_date = datetime.fromisoformat(params["end_date"]).date()
        else:
            end_date = params.get("end_date")
        
        if not start_date or not end_date:
            raise ValueError(f"Missing required dates for hotel search: start_date={params.get('start_date')}, end_date={params.get('end_date')}")
        
        hotel_results = hotels.search(
            params["city"],
            start_date,
            end_date,
            params.get("max_price", 200),
            params.get("near"),
            params.get("limit", 10)
        )
        
        return {"hotels": hotel_results}
    
    elif tool_name == "hotels.find_plan_b":
        # Handle both string and date objects
        if isinstance(params.get("start_date"), str):
            start_date = datetime.fromisoformat(params["start_date"]).date()
        else:
            start_date = params.get("start_date")
        
        if isinstance(params.get("end_date"), str):
            end_date = datetime.fromisoformat(params["end_date"]).date()
        else:
            end_date = params.get("end_date")
        
        if not start_date or not end_date:
            raise ValueError(f"Missing required dates for Plan B hotel search")
        
        plan_b_hotels = hotels.find_plan_b_hotels(
            params["city"],
            start_date,
            end_date,
            params["original_max_price"],
            params["remaining_budget"]
        )
        
        return {"hotels": plan_b_hotels, "plan_b": True}
    
    elif tool_name == "synthesis.none":
        return {"status": "ready_for_synthesis"}
    
    else:
        logger.warning(f"Unknown tool: {tool_name}")
        return {"error": f"Unknown tool: {tool_name}"}


def _process_tool_result(agent_state: AgentState, step, tool_result: ToolResult) -> AgentState:
    """Process tool result and update agent state accordingly."""
    
    if step.tool == "maps.find_directions":
        result = tool_result.output
        if result.get("status") == "success":
            distance_miles = result["distance_miles"]
            
            # Determine transport mode based on distance (with thinking)
            thinking_steps = []
            thinking_steps.append(f"🧠 Thinking: Analyzing transport options for {distance_miles:.0f} mile trip...")
            
            if distance_miles > 500:
                # Flying for long distances (>500 miles)
                thinking_steps.append(f"  📊 Distance: {distance_miles:.0f} miles (>{500} miles threshold)")
                thinking_steps.append(f"  ✈️ Flying Analysis:")
                
                # Estimate flight cost: ~$0.15-0.20 per mile per person, average $300-500 per person
                # For 2 people, estimate $600-1000 total
                flight_cost_per_person = min(500, max(300, distance_miles * 0.15))
                flight_cost = flight_cost_per_person * 2  # Assume 2 travelers
                
                # Flight duration: ~2 hours flight time + 2 hours airport time = ~4 hours total
                # Plus time based on distance (rough estimate: 1 hour per 500 miles)
                flight_time_hours = 2 + (distance_miles / 500)  # Base 2 hours + distance factor
                flight_duration_minutes = int(flight_time_hours * 60)
                driving_time_hours = result["duration_minutes"] / 60
                
                thinking_steps.append(f"    - Cost: ${flight_cost:.0f} for 2 travelers (${flight_cost_per_person:.0f}/person)")
                thinking_steps.append(f"    - Time: ~{flight_duration_minutes//60}h {flight_duration_minutes%60}m (including airport)")
                thinking_steps.append(f"    - vs Driving: {driving_time_hours:.1f}h driving, ${result['gas_estimate']:.0f} gas")
                thinking_steps.append(f"  🎯 Decision: FLYING")
                thinking_steps.append(f"    Reasoning: Distance > 500 miles makes flying faster and more practical")
                thinking_steps.append(f"    Trade-off: Higher cost (${flight_cost:.0f} vs ${result['gas_estimate']:.0f}) but saves {driving_time_hours - (flight_duration_minutes/60):.1f} hours")
                
                transport = TransportSelection(
                    mode="flying",
                    duration_minutes=flight_duration_minutes,
                    distance_miles=distance_miles,
                    cost=flight_cost,
                    details={
                        **result,
                        "flight_cost_per_person": flight_cost_per_person,
                        "airport_time": 120  # 2 hours for check-in, security, etc.
                    }
                )
                agent_state.selections.transport = transport
                
                # Update budget
                agent_state.budget_remaining -= flight_cost
                tool_result.cost_estimate = flight_cost
                tool_result.thinking = "\n".join(thinking_steps)
                tool_result.notes = f"Flying route: {distance_miles:.0f} miles, ~{flight_duration_minutes//60}h {flight_duration_minutes%60}m total time (including airport), ${flight_cost:.2f} for 2 travelers"
            else:
                # Driving for shorter distances (<=500 miles)
                thinking_steps.append(f"  📊 Distance: {distance_miles:.0f} miles (<={500} miles threshold)")
                thinking_steps.append(f"  🚗 Driving Analysis:")
                thinking_steps.append(f"    - Cost: ${result['gas_estimate']:.2f} (gas estimate)")
                thinking_steps.append(f"    - Time: {result['duration_minutes']//60}h {result['duration_minutes']%60}m")
                thinking_steps.append(f"    - Distance: {distance_miles:.1f} miles")
                thinking_steps.append(f"  🎯 Decision: DRIVING")
                thinking_steps.append(f"    Reasoning: Distance <= 500 miles makes driving cost-effective")
                thinking_steps.append(f"    Benefit: Saves ${600 - result['gas_estimate']:.0f} compared to flying for short trips")
                
                transport = TransportSelection(
                    mode="driving",
                    duration_minutes=result["duration_minutes"],
                    distance_miles=distance_miles,
                    cost=result["gas_estimate"],
                    details=result
                )
                agent_state.selections.transport = transport
                
                # Update budget
                agent_state.budget_remaining -= result["gas_estimate"]
                tool_result.cost_estimate = result["gas_estimate"]
                tool_result.thinking = "\n".join(thinking_steps)
                tool_result.notes = f"Driving route: {distance_miles:.0f} miles, {result['duration_minutes']} min, ${result['gas_estimate']:.2f} gas"
    
    elif step.tool == "weather.forecast":
        result = tool_result.output
        if result.get("status") == "success":
            tool_result.notes = f"Weather: {result['summary']}, {result['high_f']}°F/{result['low_f']}°F, {int(result['rain_chance']*100)}% rain"
    
    elif step.tool == "places.search":
        result = tool_result.output
        places_found = result.get("places", [])
        tool_result.notes = f"Found {len(places_found)} places for '{step.params.get('query', '')}'"
    
    elif step.tool in ["hotels.search", "hotels.find_plan_b"]:
        result = tool_result.output
        hotels_found = result.get("hotels", [])
        
        if hotels_found:
            # Since hotels.search() now returns only the top 1 hotel (highest rated within budget),
            # we directly use that hotel's rental price for lodging money calculation
            if len(hotels_found) == 1:
                # Direct use of top 1 hotel from Google Maps API
                top_hotel = hotels_found[0]
                thinking_reasoning = (
                    f"🧠 Thinking: Using top 1 hotel from Google Maps API search.\n"
                    f"   Selected: {top_hotel.get('name', 'Hotel')}\n"
                    f"   Rating: {top_hotel.get('rating', 0):.1f}/5.0\n"
                    f"   Rental Price: ${top_hotel.get('price_per_night', 0):.2f}/night\n"
                    f"   Total Cost: ${top_hotel.get('total_price', 0):.2f} for {top_hotel.get('nights', 1)} night(s)\n"
                    f"   Budget Impact: ${agent_state.budget_remaining - top_hotel.get('total_price', 0):.2f} remaining after booking"
                )
                best_hotel = top_hotel
            else:
                # Fallback: if multiple hotels (shouldn't happen with new implementation)
                best_hotel, thinking_reasoning = _select_best_hotel(hotels_found, agent_state)
            
            tool_result.thinking = thinking_reasoning
            
            hotel_selection = HotelSelection(
                name=best_hotel["name"],
                price_per_night=best_hotel["price_per_night"],
                total_price=best_hotel["total_price"],
                rating=best_hotel["rating"],
                lat=best_hotel["lat"],
                lng=best_hotel["lng"],
                link=best_hotel.get("link"),
                address=best_hotel.get("address")
            )
            
            # Use top 1 hotel's rental price for lodging money calculation
            rental_price_total = best_hotel["total_price"]
            agent_state.budget_remaining -= rental_price_total
            tool_result.cost_estimate = rental_price_total
            
            if result.get("plan_b"):
                agent_state.selections.hotel = hotel_selection
                tool_result.notes = f"Plan B hotel selected: {best_hotel['name']} - ${rental_price_total:.2f} total (rental price from Google Maps API)"
            else:
                agent_state.selections.hotel = hotel_selection
                tool_result.notes = f"Top 1 hotel selected: {best_hotel['name']} - ${rental_price_total:.2f} total (rental price: ${best_hotel['price_per_night']:.2f}/night)"
        else:
            tool_result.thinking = "🧠 Thinking: No hotels found within budget. May need to adjust search criteria or trigger Plan B."
            tool_result.notes = "No hotels found within budget"
    
    return agent_state


def _select_best_hotel(hotels: List[Dict[str, Any]], agent_state: AgentState) -> tuple:
    """Select the best hotel based on rating, price, and other factors.
    
    Returns:
        tuple: (selected_hotel, thinking_reasoning)
    """
    
    if not hotels:
        raise ValueError("No hotels to select from")
    
    # Agent thinking: Analyze each hotel option
    thinking_steps = []
    thinking_steps.append(f"🧠 Thinking: Evaluating {len(hotels)} hotel options...")
    
    # Score hotels based on multiple factors
    scored_hotels = []
    
    for hotel in hotels:
        score = hotels.calculate_hotel_score(hotel, [], None, None)
        price = hotel.get("price_per_night", 0)
        rating = hotel.get("rating", 0)
        
        # Boost score if hotel fits well within budget
        budget_remaining_after = agent_state.budget_remaining - hotel.get("total_price", 0)
        original_score = score
        
        if budget_remaining_after > 200:  # Good budget buffer
            score += 0.1
            thinking_steps.append(f"  ✓ {hotel.get('name', 'Hotel')}: Rating {rating:.1f}, ${price:.0f}/night - Good budget buffer (${budget_remaining_after:.0f} remaining)")
        elif budget_remaining_after < 50:  # Tight budget
            score -= 0.2
            thinking_steps.append(f"  ⚠ {hotel.get('name', 'Hotel')}: Rating {rating:.1f}, ${price:.0f}/night - Tight budget (${budget_remaining_after:.0f} remaining)")
        else:
            thinking_steps.append(f"  ✓ {hotel.get('name', 'Hotel')}: Rating {rating:.1f}, ${price:.0f}/night - Balanced choice (${budget_remaining_after:.0f} remaining)")
        
        scored_hotels.append((score, hotel, original_score))
    
    # Sort by score (highest first)
    scored_hotels.sort(key=lambda x: x[0], reverse=True)
    
    best_hotel = scored_hotels[0][1]
    best_score = scored_hotels[0][0]
    original_best_score = scored_hotels[0][2]
    
    # Final decision reasoning
    thinking_steps.append(f"\n🎯 Decision: Selected '{best_hotel.get('name', 'Hotel')}'")
    thinking_steps.append(f"   Reasoning:")
    thinking_steps.append(f"   - Quality Score: {original_best_score:.2f}/1.0 (rating + price + location)")
    thinking_steps.append(f"   - Final Score: {best_score:.2f}/1.0 (adjusted for budget fit)")
    thinking_steps.append(f"   - Price: ${best_hotel.get('price_per_night', 0):.0f}/night (${best_hotel.get('total_price', 0):.0f} total)")
    thinking_steps.append(f"   - Rating: {best_hotel.get('rating', 0):.1f}/5.0")
    thinking_steps.append(f"   - Budget Impact: ${agent_state.budget_remaining - best_hotel.get('total_price', 0):.0f} remaining after booking")
    
    # Compare with alternatives
    if len(scored_hotels) > 1:
        second_best = scored_hotels[1][1]
        thinking_steps.append(f"\n   Alternative considered: '{second_best.get('name', 'Hotel')}'")
        thinking_steps.append(f"   - Why not chosen: {'Lower score' if scored_hotels[1][0] < best_score else 'Budget constraints'}")
    
    thinking_reasoning = "\n".join(thinking_steps)
    
    return best_hotel, thinking_reasoning


def _check_constraints_and_replan(agent_state: AgentState, step, result: Dict[str, Any]) -> AgentState:
    """Check for constraint violations and trigger re-planning if needed."""
    
    # Budget constraint check
    if agent_state.budget_remaining < 100 and step.phase == "lodging" and not result.get("plan_b"):
        logger.warning(f"Budget constraint triggered: ${agent_state.budget_remaining:.2f} remaining")
        
        # Add Plan B hotel search to plan
        constraint_details = {
            "city": step.params.get("city", ""),
            "start_date": step.params.get("start_date", ""),
            "end_date": step.params.get("end_date", ""),
            "original_max_price": step.params.get("max_price", 200)
        }
        
        agent_state = update_plan_with_constraints(agent_state, "budget", constraint_details)
    
    # Weather constraint check
    if step.tool == "weather.forecast" and result.get("rain_chance", 0) > 0.5:
        logger.warning(f"Weather constraint triggered: {result.get('rain_chance', 0)*100:.0f}% rain chance")
        
        constraint_details = {
            "city": step.params.get("city", ""),
            "rain_chance": result.get("rain_chance", 0)
        }
        
        agent_state = update_plan_with_constraints(agent_state, "weather", constraint_details)
    
    return agent_state


def select_activities(agent_state: AgentState, user_interests: List[str], max_activities: int = 6, destination_city: str = None) -> AgentState:
    """
    Select final activities from all found places based on interests, weather, and budget.
    
    Args:
        agent_state: Current agent state
        user_interests: List of user interests
        max_activities: Maximum number of activities to select
        destination_city: Destination city name (for fallback activities)
    """
    logger.info(f"Selecting activities from search results for interests: {user_interests}")
    
    # Collect all places from tool results
    all_places = []
    weather_data = None
    
    for tool_result in agent_state.log:
        if tool_result.tool == "places.search":
            places_list = tool_result.output.get("places", [])
            all_places.extend(places_list)
        elif tool_result.tool == "weather.forecast":
            weather_data = tool_result.output
    
    if not all_places:
        logger.warning("No places found from API searches. Generating generic activities based on interests.")
        
        # Generate generic activities when API returns no results
        # This ensures the itinerary still has activities even if Places API fails
        generic_activities = []
        
        # Get destination city name
        if not destination_city:
            # Try to extract from places.search params in log
            for tool_result in agent_state.log:
                if tool_result.tool == "places.search":
                    destination_city = tool_result.input.get("near", "the destination")
                    break
            
            # Fallback to hotel city or generic
            if not destination_city or destination_city == "the destination":
                if agent_state.selections.hotel and agent_state.selections.hotel.address:
                    # Try to extract city from address
                    address_parts = agent_state.selections.hotel.address.split(",")
                    if len(address_parts) >= 2:
                        destination_city = address_parts[-2].strip()  # Usually city is second to last
                    else:
                        destination_city = "the destination"
                else:
                    destination_city = "the destination"
        
        # Get coordinates for the destination city
        from tools.maps import geocode_city
        city_lat, city_lng = geocode_city(destination_city)
        
        # Use hotel coordinates if available, otherwise use geocoded city coordinates
        base_lat = agent_state.selections.hotel.lat if agent_state.selections.hotel else city_lat
        base_lng = agent_state.selections.hotel.lng if agent_state.selections.hotel else city_lng
        
        # Create generic activities based on interests
        for i, interest in enumerate(user_interests[:max_activities]):
            # Generate a generic activity for each interest with slight coordinate variations
            offset_lat = base_lat + (i * 0.005)  # Spread activities around
            offset_lng = base_lng + (i * 0.005)
            
            generic_activity = {
                "name": f"{interest.title()} Venue in {destination_city}",
                "tags": [interest.lower(), "attraction"],
                "rating": 4.0,
                "price": 15.0,  # Generic price
                "lat": offset_lat,
                "lng": offset_lng,
                "place_id": f"generic_{interest}_{i}",
                "link": None,
                "address": f"Various locations in {destination_city}"
            }
            generic_activities.append(generic_activity)
        
        # If no interests, create some generic activities
        if not generic_activities:
            generic_activities = [
                {
                    "name": f"Local Attractions in {destination_city}",
                    "tags": ["attraction", "sightseeing"],
                    "rating": 4.0,
                    "price": 20.0,
                    "lat": base_lat + 0.01,
                    "lng": base_lng + 0.01,
                    "place_id": "generic_attraction_1",
                    "link": None,
                    "address": f"Various locations in {destination_city}"
                },
                {
                    "name": f"Restaurants in {destination_city}",
                    "tags": ["restaurant", "dining"],
                    "rating": 4.0,
                    "price": 25.0,
                    "lat": base_lat - 0.01,
                    "lng": base_lng - 0.01,
                    "place_id": "generic_restaurant_1",
                    "link": None,
                    "address": f"Various locations in {destination_city}"
                }
            ]
        
        all_places = generic_activities
        logger.info(f"Generated {len(generic_activities)} generic activities as fallback")
    
    # Remove duplicates based on place_id
    unique_places = {}
    for place in all_places:
        place_id = place.get("place_id", place.get("name", ""))
        if place_id not in unique_places:
            unique_places[place_id] = place
    
    all_places = list(unique_places.values())
    
    # Find overlapping interests (places that match multiple interests)
    multi_interest_places = places.find_overlapping_interests(all_places, user_interests)
    
    # Filter by location if hotel is selected
    if agent_state.selections.hotel:
        nearby_places = places.filter_by_location(
            all_places,
            agent_state.selections.hotel.lat,
            agent_state.selections.hotel.lng,
            max_distance_miles=5.0
        )
    else:
        nearby_places = all_places
    
    # Handle weather constraints
    selected_places = []
    is_rainy = weather_data and weather_data.get("rain_chance", 0) > 0.5
    
    if is_rainy:
        # Prefer indoor activities
        indoor_places = [p for p in nearby_places if any(tag in ["indoor", "museum", "coffee", "restaurant", "bar"] for tag in p.get("tags", []))]
        selected_places.extend(indoor_places[:4])  # 4 indoor activities
        
        # Add 1-2 outdoor activities as backup
        outdoor_places = [p for p in nearby_places if p not in selected_places]
        selected_places.extend(outdoor_places[:2])
        
        # Log weather re-planning
        weather_note = f"Weather re-plan: Selected {len(indoor_places)} indoor activities due to {weather_data.get('rain_chance')*100:.0f}% rain chance"
        weather_tool_result = ToolResult(
            tool="weather.replan",
            input={"rain_chance": weather_data.get("rain_chance")},
            output={"indoor_selected": len(indoor_places), "outdoor_backup": len(outdoor_places)},
            cost_estimate=0.0,
            notes=weather_note
        )
        agent_state.log.append(weather_tool_result)
    else:
        # Normal selection - prioritize multi-interest places
        selected_places.extend(multi_interest_places[:3])
        
        # Add other high-rated places
        remaining_places = [p for p in nearby_places if p not in selected_places]
        remaining_places.sort(key=lambda x: x.get("rating", 0), reverse=True)
        selected_places.extend(remaining_places[:max_activities-len(selected_places)])
    
    # Limit to max activities and budget
    final_activities = []
    total_activity_cost = 0.0
    
    # Calculate available budget for activities
    # Use remaining budget, but ensure it's at least 0 (don't use negative budget)
    # If budget is negative, we'll prioritize free activities and low-cost activities
    activity_budget = max(0.0, agent_state.budget_remaining - 50)  # Leave $50 buffer, but don't go negative
    
    # Get number of travelers from agent state if available, otherwise default to 2
    # Note: We need to pass travelers count through the function, but for now assume 2
    num_travelers = 2  # Default to 2 travelers
    
    logger.info(f"🎯 Activity Selection Budget: ${activity_budget:.2f} (remaining: ${agent_state.budget_remaining:.2f})")
    
    # Separate free and paid activities
    free_places = []
    paid_places = []
    
    for place in selected_places[:max_activities * 2]:  # Look at more places to find free ones
        # Get price from place data - handle None, 0, and missing keys properly
        place_price = place.get("price")
        
        # Check if price is valid
        if place_price is None:
            # Price key doesn't exist or is None - check if it's a free activity by name/tags
            place_name_lower = place.get("name", "").lower()
            place_tags_lower = [tag.lower() for tag in place.get("tags", [])]
            
            # Common free activity indicators
            free_indicators = ["park", "trail", "beach", "plaza", "square", "bridge", "viewpoint", "monument"]
            is_likely_free = any(indicator in place_name_lower for indicator in free_indicators) or \
                           any(indicator in " ".join(place_tags_lower) for indicator in free_indicators)
            
            if is_likely_free:
                place_price = 0.0
                logger.info(f"Activity '{place.get('name')}' appears to be free (no price, but matches free activity patterns)")
            else:
                place_price = 15.0  # Default for paid activities
                logger.debug(f"Activity '{place.get('name')}' has no price, using default $15.0/person")
        elif isinstance(place_price, (int, float)):
            if place_price < 0:
                place_price = 15.0
                logger.warning(f"Activity '{place.get('name')}' has negative price, using default $15.0/person")
            elif place_price == 0.0:
                # Valid free activity
                logger.debug(f"Activity '{place.get('name')}' is free (price: $0.0/person)")
            # else: valid paid activity with price > 0
        else:
            # Invalid price type
            place_price = 15.0
            logger.warning(f"Activity '{place.get('name')}' has invalid price type {type(place_price)}, using default $15.0/person")
        
        # Categorize as free or paid
        if place_price == 0.0:
            free_places.append((place, place_price))
        else:
            paid_places.append((place, place_price))
    
    # Always add free activities first (they don't cost anything)
    for place, place_price in free_places[:max_activities]:
        activity = ActivitySelection(
            name=place["name"],
            tags=place.get("tags", []),
            rating=place.get("rating", 4.0),
            price=0.0,  # Explicitly set to 0.0 for free activities
            lat=place["lat"],
            lng=place["lng"],
            place_id=place.get("place_id"),
            link=place.get("link"),
            address=place.get("address")
        )
        final_activities.append(activity)
        logger.info(f"✓ Added FREE activity: '{place['name']}' (price: $0.00/person)")
    
    # Then add paid activities that fit within budget
    for place, place_price in paid_places:
        if len(final_activities) >= max_activities:
            break
        
        place_cost = place_price * num_travelers
        
        # Check if we can afford this activity
        if total_activity_cost + place_cost <= activity_budget:
            activity = ActivitySelection(
                name=place["name"],
                tags=place.get("tags", []),
                rating=place.get("rating", 4.0),
                price=float(place_price),
                lat=place["lat"],
                lng=place["lng"],
                place_id=place.get("place_id"),
                link=place.get("link"),
                address=place.get("address")
            )
            final_activities.append(activity)
            total_activity_cost += place_cost
            logger.info(f"✓ Added PAID activity: '{place['name']}' - Price: ${place_price:.2f}/person, Cost: ${place_cost:.2f} total (${total_activity_cost:.2f} cumulative)")
        else:
            logger.debug(f"⊘ Skipped paid activity '{place['name']}' - would exceed budget (${total_activity_cost + place_cost:.2f} > ${activity_budget:.2f})")
    
    # If we still don't have enough activities and budget allows, add more free activities
    if len(final_activities) < max_activities and len(free_places) > len([a for a in final_activities if a.price == 0.0]):
        remaining_free = [p for p in free_places if p[0]["name"] not in [a.name for a in final_activities]]
        for place, place_price in remaining_free[:max_activities - len(final_activities)]:
            activity = ActivitySelection(
                name=place["name"],
                tags=place.get("tags", []),
                rating=place.get("rating", 4.0),
                price=0.0,
                lat=place["lat"],
                lng=place["lng"],
                place_id=place.get("place_id"),
                link=place.get("link"),
                address=place.get("address")
            )
            final_activities.append(activity)
            logger.info(f"✓ Added additional FREE activity: '{place['name']}'")
    
    # Update agent state
    agent_state.selections.activities = final_activities
    agent_state.budget_remaining -= total_activity_cost
    
    # Log activity selection
    if len(final_activities) == 0:
        logger.warning(f"No activities selected! Available places: {len(selected_places)}, Budget: ${activity_budget:.2f}")
        selection_notes = f"No activities selected (budget: ${activity_budget:.2f}, found {len(selected_places)} places)"
    else:
        selection_notes = f"Selected {len(final_activities)} activities for ${total_activity_cost:.2f} total"
        if multi_interest_places:
            multi_count = len([p for p in final_activities if p.name in [mp['name'] for mp in multi_interest_places]])
            if multi_count > 0:
                selection_notes += f" (including {multi_count} multi-interest matches)"
    
    activity_tool_result = ToolResult(
        tool="activities.select",
        input={"interests": user_interests, "max_activities": max_activities},
        output={"selected": len(final_activities), "total_cost": total_activity_cost, "activities": [a.name for a in final_activities]},
        cost_estimate=total_activity_cost,
        notes=selection_notes
    )
    agent_state.log.append(activity_tool_result)
    
    logger.info(f"Activity selection complete: {len(final_activities)} activities selected, ${total_activity_cost:.2f} total cost, ${agent_state.budget_remaining:.2f} remaining budget")
    
    return agent_state


def validate_selections(agent_state: AgentState) -> List[str]:
    """Validate that all required selections have been made."""
    issues = []
    
    if not agent_state.selections.transport:
        issues.append("No transport option selected")
    
    if not agent_state.selections.hotel:
        issues.append("No hotel selected")
    
    if not agent_state.selections.activities:
        issues.append("No activities selected")
    
    if agent_state.budget_remaining < 0:
        issues.append(f"Budget exceeded by ${abs(agent_state.budget_remaining):.2f}")
    
    return issues
