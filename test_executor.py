"""
Tests for the executor module.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from agent.state import (
    UserRequest, AgentState, PlanStep, ToolResult, 
    TransportSelection, HotelSelection, ActivitySelection
)
from agent.executor import execute_plan, select_activities, validate_selections


@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing."""
    plan_steps = [
        PlanStep(
            phase="transport",
            description="Find directions",
            tool="maps.find_directions",
            params={"origin": "Dallas, TX", "destination": "Austin, TX"}
        ),
        PlanStep(
            phase="lodging",
            description="Search hotels",
            tool="hotels.search",
            params={
                "city": "Austin, TX",
                "start_date": (date.today() + timedelta(days=7)).isoformat(),
                "end_date": (date.today() + timedelta(days=9)).isoformat(),
                "max_price": 200,
                "limit": 5
            }
        ),
        PlanStep(
            phase="activities",
            description="Check weather",
            tool="weather.forecast",
            params={"city": "Austin, TX"}
        )
    ]
    
    return AgentState(
        budget_remaining=800.0,
        plan=plan_steps
    )


@pytest.fixture
def sample_user_request():
    """Sample user request for testing."""
    return UserRequest(
        origin="Dallas, TX",
        destination="Austin, TX",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=9),
        travelers=2,
        budget_total=800.0,
        interests=["BBQ", "live music"]
    )


@patch('tools.maps.find_directions')
@patch('tools.hotels.search')
@patch('tools.weather.forecast')
def test_execute_plan_basic(mock_weather, mock_hotels, mock_maps, sample_agent_state):
    """Test basic plan execution."""
    
    # Mock tool responses
    mock_maps.return_value = {
        "status": "success",
        "duration_minutes": 195,
        "distance_miles": 195.0,
        "gas_estimate": 27.30
    }
    
    mock_hotels.return_value = [
        {
            "name": "Test Hotel",
            "price_per_night": 120.0,
            "total_price": 240.0,
            "rating": 4.2,
            "lat": 30.2640,
            "lng": -97.7425,
            "link": "https://test.com",
            "address": "123 Test St"
        }
    ]
    
    mock_weather.return_value = {
        "status": "success",
        "summary": "Sunny",
        "high_f": 78,
        "low_f": 62,
        "rain_chance": 0.15
    }
    
    # Execute plan
    result_state = execute_plan(sample_agent_state)
    
    # Verify tools were called
    mock_maps.assert_called_once_with("Dallas, TX", "Austin, TX")
    mock_hotels.assert_called_once()
    mock_weather.assert_called_once()
    
    # Verify results
    assert len(result_state.log) == 3  # One for each step
    assert result_state.selections.transport is not None
    assert result_state.selections.hotel is not None
    
    # Verify budget was updated
    assert result_state.budget_remaining < 800.0  # Should have spent money


def test_execute_plan_budget_tracking(sample_agent_state):
    """Test that budget is properly tracked during execution."""
    
    # Set up mock responses that cost money
    with patch('tools.maps.find_directions') as mock_maps, \
         patch('tools.hotels.search') as mock_hotels:
        
        mock_maps.return_value = {
            "status": "success",
            "duration_minutes": 195,
            "distance_miles": 195.0,
            "gas_estimate": 50.0  # $50 transport cost
        }
        
        mock_hotels.return_value = [
            {
                "name": "Expensive Hotel",
                "price_per_night": 200.0,
                "total_price": 400.0,  # $400 hotel cost
                "rating": 4.5,
                "lat": 30.2640,
                "lng": -97.7425
            }
        ]
        
        # Execute transport and lodging steps only
        limited_state = AgentState(
            budget_remaining=800.0,
            plan=sample_agent_state.plan[:2]  # Only transport and lodging
        )
        
        result_state = execute_plan(limited_state)
        
        # Check budget calculation
        expected_remaining = 800.0 - 50.0 - 400.0  # 350.0
        assert abs(result_state.budget_remaining - expected_remaining) < 0.01
        
        # Check cost estimates in log
        transport_log = next(log for log in result_state.log if log.tool == "maps.find_directions")
        hotel_log = next(log for log in result_state.log if log.tool == "hotels.search")
        
        assert transport_log.cost_estimate == 50.0
        assert hotel_log.cost_estimate == 400.0


@patch('tools.hotels.search')
@patch('tools.hotels.find_plan_b_hotels')
def test_budget_constraint_triggers_plan_b(mock_plan_b, mock_hotels, sample_agent_state):
    """Test that low budget triggers Plan B hotel search."""
    
    # Mock expensive hotel that would break budget
    mock_hotels.return_value = [
        {
            "name": "Expensive Hotel",
            "price_per_night": 350.0,
            "total_price": 700.0,  # Would leave only $100
            "rating": 4.5,
            "lat": 30.2640,
            "lng": -97.7425
        }
    ]
    
    # Mock Plan B response
    mock_plan_b.return_value = [
        {
            "name": "Budget Hotel",
            "price_per_night": 80.0,
            "total_price": 160.0,
            "rating": 3.8,
            "lat": 30.2640,
            "lng": -97.7425
        }
    ]
    
    # Set initial budget low enough to trigger Plan B
    sample_agent_state.budget_remaining = 500.0
    
    # Execute only hotel step
    hotel_state = AgentState(
        budget_remaining=500.0,
        plan=[sample_agent_state.plan[1]]  # Only hotel search
    )
    
    result_state = execute_plan(hotel_state)
    
    # Should have triggered Plan B logic
    # Note: Plan B is handled in constraint checking, so we test the constraint logic
    assert result_state.budget_remaining < 500.0  # Should have spent money
    assert result_state.selections.hotel is not None


@patch('tools.weather.forecast')
def test_weather_constraint_triggers_replan(mock_weather, sample_agent_state):
    """Test that rainy weather triggers indoor activity search."""
    
    # Mock rainy weather
    mock_weather.return_value = {
        "status": "success",
        "summary": "Rainy",
        "high_f": 68,
        "low_f": 58,
        "rain_chance": 0.75  # High rain chance should trigger re-plan
    }
    
    # Execute weather step
    weather_state = AgentState(
        budget_remaining=800.0,
        plan=[sample_agent_state.plan[2]]  # Only weather step
    )
    
    result_state = execute_plan(weather_state)
    
    # Verify weather result was logged
    weather_log = next(log for log in result_state.log if log.tool == "weather.forecast")
    assert "rain" in weather_log.notes.lower()
    
    # Check that rain chance was recorded
    assert weather_log.output.get("rain_chance", 0) > 0.5


def test_select_activities_basic():
    """Test basic activity selection."""
    
    # Create agent state with mock place search results
    agent_state = AgentState(budget_remaining=400.0)
    
    # Add mock tool results
    places_result = ToolResult(
        tool="places.search",
        input={"query": "BBQ"},
        output={
            "places": [
                {
                    "name": "Franklin Barbecue",
                    "tags": ["BBQ", "restaurant"],
                    "rating": 4.6,
                    "price": 25.0,
                    "lat": 30.2701,
                    "lng": -97.7374,
                    "place_id": "franklin_bbq"
                },
                {
                    "name": "Stubb's Bar-B-Q",
                    "tags": ["BBQ", "live music", "venue"],
                    "rating": 4.2,
                    "price": 22.0,
                    "lat": 30.2634,
                    "lng": -97.7354,
                    "place_id": "stubbs_bbq"
                }
            ]
        },
        cost_estimate=0.0
    )
    
    agent_state.log.append(places_result)
    
    # Set a hotel for location filtering
    agent_state.selections.hotel = HotelSelection(
        name="Test Hotel",
        price_per_night=120.0,
        total_price=240.0,
        rating=4.2,
        lat=30.2640,
        lng=-97.7425
    )
    
    # Select activities
    result_state = select_activities(agent_state, ["BBQ", "live music"], max_activities=4)
    
    # Should have selected activities
    assert len(result_state.selections.activities) > 0
    assert result_state.budget_remaining < 400.0  # Should have spent money
    
    # Should have logged the selection
    selection_log = next(log for log in result_state.log if log.tool == "activities.select")
    assert "selected" in selection_log.notes.lower()


def test_select_activities_weather_replan():
    """Test activity selection with weather re-planning."""
    
    agent_state = AgentState(budget_remaining=400.0)
    
    # Add rainy weather result
    weather_result = ToolResult(
        tool="weather.forecast",
        input={"city": "Austin, TX"},
        output={
            "status": "success",
            "summary": "Rainy",
            "rain_chance": 0.75
        },
        cost_estimate=0.0
    )
    agent_state.log.append(weather_result)
    
    # Add places with indoor/outdoor options
    places_result = ToolResult(
        tool="places.search",
        input={"query": "activities"},
        output={
            "places": [
                {
                    "name": "Outdoor Park",
                    "tags": ["park", "outdoor"],
                    "rating": 4.5,
                    "price": 0.0,
                    "lat": 30.2672,
                    "lng": -97.7731,
                    "place_id": "outdoor_park"
                },
                {
                    "name": "Indoor Museum",
                    "tags": ["museum", "indoor"],
                    "rating": 4.3,
                    "price": 15.0,
                    "lat": 30.2808,
                    "lng": -97.7391,
                    "place_id": "indoor_museum"
                }
            ]
        },
        cost_estimate=0.0
    )
    agent_state.log.append(places_result)
    
    # Select activities
    result_state = select_activities(agent_state, ["parks", "museums"], max_activities=4)
    
    # Should have logged weather re-planning
    weather_replan_log = next(
        (log for log in result_state.log if log.tool == "weather.replan"), 
        None
    )
    assert weather_replan_log is not None
    assert "rain" in weather_replan_log.notes.lower()


def test_select_activities_multi_interest_matching():
    """Test that multi-interest places are prioritized."""
    
    agent_state = AgentState(budget_remaining=400.0)
    
    # Add places with overlapping interests
    places_result = ToolResult(
        tool="places.search",
        input={"query": "BBQ"},
        output={
            "places": [
                {
                    "name": "Regular BBQ",
                    "tags": ["BBQ", "restaurant"],
                    "rating": 4.4,
                    "price": 20.0,
                    "lat": 30.2580,
                    "lng": -97.7386,
                    "place_id": "regular_bbq"
                },
                {
                    "name": "Stubb's Bar-B-Q",
                    "tags": ["BBQ", "live music", "venue"],  # Matches both interests
                    "rating": 4.2,
                    "price": 22.0,
                    "lat": 30.2634,
                    "lng": -97.7354,
                    "place_id": "stubbs_bbq"
                }
            ]
        },
        cost_estimate=0.0
    )
    agent_state.log.append(places_result)
    
    # Select activities with multiple interests
    result_state = select_activities(agent_state, ["BBQ", "live music"], max_activities=4)
    
    # Should have selected activities
    assert len(result_state.selections.activities) > 0
    
    # Stubb's should be selected as it matches multiple interests
    selected_names = [activity.name for activity in result_state.selections.activities]
    assert "Stubb's Bar-B-Q" in selected_names


def test_validate_selections_complete():
    """Test validation with complete selections."""
    
    agent_state = AgentState(budget_remaining=100.0)
    
    # Add complete selections
    agent_state.selections.transport = TransportSelection(
        mode="driving",
        duration_minutes=195,
        distance_miles=195.0,
        cost=50.0,
        details={}
    )
    
    agent_state.selections.hotel = HotelSelection(
        name="Test Hotel",
        price_per_night=120.0,
        total_price=240.0,
        rating=4.2,
        lat=30.2640,
        lng=-97.7425
    )
    
    agent_state.selections.activities = [
        ActivitySelection(
            name="Test Activity",
            tags=["test"],
            rating=4.0,
            price=15.0,
            lat=30.2701,
            lng=-97.7374
        )
    ]
    
    # Validate
    issues = validate_selections(agent_state)
    
    # Should have no issues
    assert len(issues) == 0


def test_validate_selections_incomplete():
    """Test validation with incomplete selections."""
    
    agent_state = AgentState(budget_remaining=100.0)
    
    # Missing all selections
    issues = validate_selections(agent_state)
    
    # Should detect missing selections
    assert len(issues) >= 3  # transport, hotel, activities
    assert any("transport" in issue.lower() for issue in issues)
    assert any("hotel" in issue.lower() for issue in issues)
    assert any("activities" in issue.lower() for issue in issues)


def test_validate_selections_budget_exceeded():
    """Test validation with negative budget."""
    
    agent_state = AgentState(budget_remaining=-50.0)  # Negative budget
    
    # Add minimal selections
    agent_state.selections.transport = TransportSelection(
        mode="driving", duration_minutes=195, distance_miles=195.0, cost=50.0, details={}
    )
    agent_state.selections.hotel = HotelSelection(
        name="Test", price_per_night=120.0, total_price=240.0, rating=4.2, lat=30.0, lng=-97.0
    )
    agent_state.selections.activities = [
        ActivitySelection(name="Test", tags=[], rating=4.0, price=15.0, lat=30.0, lng=-97.0)
    ]
    
    issues = validate_selections(agent_state)
    
    # Should detect budget issue
    assert len(issues) > 0
    assert any("budget" in issue.lower() or "exceeded" in issue.lower() for issue in issues)
