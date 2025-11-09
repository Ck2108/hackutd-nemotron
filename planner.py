"""
Planner module for creating ordered execution steps and budget allocations.
"""
import logging
from datetime import date, timedelta
from typing import List
from .state import UserRequest, AgentState, PlanStep, BudgetAllocation, PlanningResponse
from .llm import get_json_completion

logger = logging.getLogger(__name__)


def create_plan(user_request: UserRequest) -> AgentState:
    """
    Create an ordered execution plan with budget allocations.
    Returns AgentState with plan steps and initial budget allocation.
    """
    logger.info(f"Creating plan for trip from {user_request.origin} to {user_request.destination}")
    
    # Calculate trip duration
    trip_days = (user_request.end_date - user_request.start_date).days
    if trip_days <= 0:
        trip_days = 1
    
    # Build prompt for LLM planning
    prompt = f"""
Plan a trip itinerary with the following details:
- Origin: {user_request.origin}
- Destination: {user_request.destination}
- Start Date: {user_request.start_date}
- End Date: {user_request.end_date}
- Duration: {trip_days} days
- Travelers: {user_request.travelers}
- Total Budget: ${user_request.budget_total}
- Interests: {', '.join(user_request.interests) if user_request.interests else 'None specified'}

Create an ordered execution plan with these phases:
1. Transport - Find directions and travel costs
2. Lodging - Search for hotels within budget
3. Activities - Check weather and find activities matching interests
4. Synthesis - Create final itinerary

AVAILABLE TOOLS (you MUST use these exact tool names):
- "maps.find_directions" - For transport phase. Params: {{"origin": "string", "destination": "string"}}
- "hotels.search" - For lodging phase. Params: {{"city": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "max_price": number, "limit": number}}
- "weather.forecast" - For activities phase. Params: {{"city": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
- "places.search" - For activities phase. Params: {{"query": "string", "near": "string", "limit": number}}
- "synthesis.none" - For synthesis phase. Params: {{}}

IMPORTANT: You MUST use the exact tool names listed above. Do not invent new tool names.

For budget allocation:
- Transport: Estimate costs based on distance:
  * If distance > 500 miles: Flying (~$600-1000 for 2 people)
  * If distance <= 500 miles: Driving (~$30-50 for gas)
- Lodging: Allocate 50-60% of remaining budget after transport
- Activities: Reserve at least $150 for activities and food

Return the plan as structured JSON matching the schema exactly.
"""
    
    # Define JSON schema for structured response
    schema = {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "phase": {
                            "type": "string",
                            "enum": ["transport", "lodging", "activities", "synthesis"]
                        },
                        "description": {"type": "string"},
                        "tool": {
                            "type": "string",
                            "enum": ["maps.find_directions", "hotels.search", "hotels.find_plan_b", "weather.forecast", "places.search", "synthesis.none"],
                            "description": "Must be one of the exact tool names: maps.find_directions, hotels.search, weather.forecast, places.search, or synthesis.none"
                        },
                        "params": {"type": "object"}
                    },
                    "required": ["phase", "description", "tool", "params"]
                }
            },
            "allocations": {
                "type": "object",
                "properties": {
                    "transport": {"type": "number"},
                    "lodging_target": {"type": "number"},
                    "activities_buffer": {"type": "number"}
                },
                "required": ["transport", "lodging_target", "activities_buffer"]
            },
            "reasoning": {"type": "string"}
        },
        "required": ["steps", "allocations"]
    }
    
    # Get structured response from LLM
    try:
        response_data = get_json_completion(prompt, schema)
        
        # Validate and fix tool names if needed, and validate against user_request
        if "steps" in response_data:
            origin_mismatch = False
            destination_mismatch = False
            
            for step in response_data["steps"]:
                tool_name = step.get("tool", "")
                params = step.get("params", {})
                
                # Map common incorrect tool names to correct ones
                tool_mapping = {
                    "google maps": "maps.find_directions",
                    "maps": "maps.find_directions",
                    "directions": "maps.find_directions",
                    "booking.com": "hotels.search",
                    "hotels": "hotels.search",
                    "hotel search": "hotels.search",
                    "weather.com": "weather.forecast",
                    "weather": "weather.forecast",
                    "forecast": "weather.forecast",
                    "yelp": "places.search",
                    "places": "places.search",
                    "search": "places.search",
                    "activities": "places.search"
                }
                if tool_name.lower() in tool_mapping:
                    logger.warning(f"Fixed invalid tool name '{tool_name}' to '{tool_mapping[tool_name.lower()]}'")
                    step["tool"] = tool_mapping[tool_name.lower()]
                elif tool_name not in ["maps.find_directions", "hotels.search", "hotels.find_plan_b", "weather.forecast", "places.search", "synthesis.none"]:
                    logger.error(f"Invalid tool name '{tool_name}' in plan, using fallback")
                    raise ValueError(f"Invalid tool name: {tool_name}")
                
                # Validate that params match user_request
                if tool_name == "maps.find_directions":
                    if params.get("origin", "").lower() != user_request.origin.lower():
                        origin_mismatch = True
                        logger.warning(f"Origin mismatch: LLM returned '{params.get('origin')}' but user requested '{user_request.origin}'")
                    if params.get("destination", "").lower() != user_request.destination.lower():
                        destination_mismatch = True
                        logger.warning(f"Destination mismatch: LLM returned '{params.get('destination')}' but user requested '{user_request.destination}'")
                
                # Fix params to match user_request
                if tool_name == "maps.find_directions":
                    params["origin"] = user_request.origin
                    params["destination"] = user_request.destination
                elif tool_name == "hotels.search":
                    params["city"] = user_request.destination
                    if "start_date" not in params or params.get("start_date") != user_request.start_date.isoformat():
                        params["start_date"] = user_request.start_date.isoformat()
                    if "end_date" not in params or params.get("end_date") != user_request.end_date.isoformat():
                        params["end_date"] = user_request.end_date.isoformat()
                elif tool_name == "weather.forecast":
                    params["city"] = user_request.destination
                    if "start_date" not in params or params.get("start_date") != user_request.start_date.isoformat():
                        params["start_date"] = user_request.start_date.isoformat()
                    if "end_date" not in params or params.get("end_date") != user_request.end_date.isoformat():
                        params["end_date"] = user_request.end_date.isoformat()
                elif tool_name == "places.search":
                    params["near"] = user_request.destination
            
            # If there were mismatches, log but continue (we've fixed them)
            if origin_mismatch or destination_mismatch:
                logger.warning("LLM returned incorrect origin/destination values. Fixed to match user request.")
        
        planning_response = PlanningResponse(**response_data)
        
        # PlanningResponse already converts steps and allocations via Pydantic
        plan_steps = planning_response.steps
        allocations = planning_response.allocations
        
        logger.info(f"Created plan with {len(plan_steps)} steps")
        
    except Exception as e:
        logger.error(f"LLM planning failed, using fallback: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        plan_steps, allocations = _create_fallback_plan(user_request)
    
    # Create initial agent state
    agent_state = AgentState(
        budget_remaining=user_request.budget_total,
        plan=plan_steps,
        allocations=allocations
    )
    
    return agent_state


def _create_fallback_plan(user_request: UserRequest) -> tuple[List[PlanStep], BudgetAllocation]:
    """Create a deterministic fallback plan when LLM is unavailable."""
    
    # Calculate trip duration
    trip_days = (user_request.end_date - user_request.start_date).days
    if trip_days <= 0:
        trip_days = 1
    
    # Create ordered steps
    steps = [
        PlanStep(
            phase="transport",
            description=f"Find driving directions from {user_request.origin} to {user_request.destination}",
            tool="maps.find_directions",
            params={
                "origin": user_request.origin,
                "destination": user_request.destination
            }
        ),
        PlanStep(
            phase="lodging",
            description=f"Search for hotels in {user_request.destination}",
            tool="hotels.search",
            params={
                "city": user_request.destination,
                "start_date": user_request.start_date.isoformat(),
                "end_date": user_request.end_date.isoformat(),
                "max_price": 200.0,  # Will be updated based on budget
                "limit": 5
            }
        ),
        PlanStep(
            phase="activities",
            description=f"Check weather forecast for {user_request.destination}",
            tool="weather.forecast",
            params={
                "city": user_request.destination,
                "start_date": user_request.start_date.isoformat(),
                "end_date": user_request.end_date.isoformat()
            }
        )
    ]
    
    # Add activity searches based on interests
    for interest in user_request.interests[:3]:  # Limit to top 3 interests
        steps.append(
            PlanStep(
                phase="activities",
                description=f"Search for {interest} activities in {user_request.destination}",
                tool="places.search",
                params={
                    "query": interest,
                    "near": user_request.destination,
                    "limit": 10
                }
            )
        )
    
    # Add synthesis step
    steps.append(
        PlanStep(
            phase="synthesis",
            description="Create final itinerary with selected activities and budget breakdown",
            tool="synthesis.none",
            params={}
        )
    )
    
    # Calculate budget allocations
    total_budget = user_request.budget_total
    
    # Estimate transport cost (driving assumption)
    transport_estimate = min(50.0, total_budget * 0.1)  # 10% or $50, whichever is less
    
    # Lodging gets majority of remaining budget
    remaining_after_transport = total_budget - transport_estimate
    lodging_target = remaining_after_transport * 0.6  # 60% of remaining
    
    # Activities buffer (at least $150 or 20% of total budget)
    activities_buffer = max(150.0, total_budget * 0.2)
    
    allocations = BudgetAllocation(
        transport=transport_estimate,
        lodging_target=lodging_target,
        activities_buffer=activities_buffer
    )
    
    logger.info(f"Created fallback plan with {len(steps)} steps")
    logger.info(f"Budget allocation: Transport ${transport_estimate}, Lodging ${lodging_target}, Activities ${activities_buffer}")
    
    return steps, allocations


def update_plan_with_constraints(agent_state: AgentState, constraint_type: str, details: dict) -> AgentState:
    """
    Update the execution plan based on constraint violations.
    
    Args:
        agent_state: Current agent state
        constraint_type: Type of constraint ('budget', 'weather', 'time', 'geo')
        details: Details about the constraint violation
    
    Returns:
        Updated agent state with modified plan
    """
    logger.info(f"Updating plan due to {constraint_type} constraint: {details}")
    
    if constraint_type == "budget" and agent_state.budget_remaining < 100:
        # Add hotel Plan B step
        plan_b_step = PlanStep(
            phase="lodging",
            description="Search for cheaper hotel options (Plan B)",
            tool="hotels.find_plan_b",
            params={
                "city": details.get("city", ""),
                "start_date": details.get("start_date", ""),
                "end_date": details.get("end_date", ""),
                "original_max_price": details.get("original_max_price", 200),
                "remaining_budget": agent_state.budget_remaining
            }
        )
        
        # Insert Plan B step after regular hotel search
        lodging_index = next(
            (i for i, step in enumerate(agent_state.plan) 
             if step.phase == "lodging" and "plan_b" not in step.tool.lower()), 
            -1
        )
        
        if lodging_index >= 0:
            agent_state.plan.insert(lodging_index + 1, plan_b_step)
    
    elif constraint_type == "weather" and details.get("rain_chance", 0) > 0.5:
        # Add indoor activity search
        indoor_step = PlanStep(
            phase="activities",
            description="Search for indoor activities due to rain",
            tool="places.search",
            params={
                "query": "indoor museum coffee restaurant",
                "near": details.get("city", ""),
                "limit": 8
            }
        )
        
        # Add after weather check
        weather_index = next(
            (i for i, step in enumerate(agent_state.plan) 
             if step.tool == "weather.forecast"), 
            -1
        )
        
        if weather_index >= 0:
            agent_state.plan.insert(weather_index + 1, indoor_step)
    
    elif constraint_type == "geo":
        # Add step to find closer alternatives
        proximity_step = PlanStep(
            phase="activities",
            description="Find activities closer to hotel",
            tool="places.filter_by_location",
            params={
                "center_lat": details.get("hotel_lat"),
                "center_lng": details.get("hotel_lng"),
                "max_distance_miles": 3.0
            }
        )
        
        agent_state.plan.append(proximity_step)
    
    return agent_state


def estimate_plan_duration(plan_steps: List[PlanStep]) -> int:
    """Estimate total execution time for the plan in minutes."""
    
    duration_estimates = {
        "maps.find_directions": 2,
        "hotels.search": 3,
        "weather.forecast": 1,
        "places.search": 2,
        "synthesis.none": 5
    }
    
    total_minutes = 0
    for step in plan_steps:
        tool_time = duration_estimates.get(step.tool, 2)
        total_minutes += tool_time
    
    return total_minutes


def validate_plan(agent_state: AgentState) -> List[str]:
    """
    Validate the execution plan for completeness and logical order.
    Returns list of validation issues.
    """
    issues = []
    
    # Check for required phases
    phases_present = {step.phase for step in agent_state.plan}
    required_phases = {"transport", "lodging", "activities", "synthesis"}
    
    missing_phases = required_phases - phases_present
    if missing_phases:
        issues.append(f"Missing required phases: {', '.join(missing_phases)}")
    
    # Check phase order
    phase_order = [step.phase for step in agent_state.plan]
    if phase_order:
        if phase_order[0] != "transport":
            issues.append("Plan should start with transport phase")
        
        if "synthesis" in phase_order and phase_order[-1] != "synthesis":
            issues.append("Synthesis should be the final phase")
    
    # Check budget allocation
    if agent_state.allocations:
        total_allocated = (
            agent_state.allocations.transport +
            agent_state.allocations.lodging_target +
            agent_state.allocations.activities_buffer
        )
        
        if total_allocated > agent_state.budget_remaining * 1.2:  # Allow 20% buffer
            issues.append("Budget allocation exceeds available budget")
    
    return issues
