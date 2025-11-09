"""
Tests for the planner module.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from agent.state import UserRequest, PlanStep, BudgetAllocation
from agent.planner import create_plan, validate_plan, estimate_plan_duration


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


def test_create_plan_structure(sample_user_request):
    """Test that create_plan returns proper structure."""
    agent_state = create_plan(sample_user_request)
    
    # Check basic structure
    assert agent_state is not None
    assert agent_state.budget_remaining == 800.0
    assert len(agent_state.plan) > 0
    assert agent_state.allocations is not None
    
    # Check plan phases are in correct order
    phases = [step.phase for step in agent_state.plan]
    
    # Transport should be first
    assert phases[0] == "transport"
    
    # Should have all required phases
    required_phases = {"transport", "lodging", "activities", "synthesis"}
    plan_phases = set(phases)
    assert required_phases.issubset(plan_phases)


def test_create_plan_tool_assignments(sample_user_request):
    """Test that plan steps have correct tool assignments."""
    agent_state = create_plan(sample_user_request)
    
    # Check tool assignments by phase
    phase_tools = {}
    for step in agent_state.plan:
        if step.phase not in phase_tools:
            phase_tools[step.phase] = []
        phase_tools[step.phase].append(step.tool)
    
    # Transport phase should use maps tool
    assert any("maps" in tool for tool in phase_tools.get("transport", []))
    
    # Lodging phase should use hotels tool
    assert any("hotels" in tool for tool in phase_tools.get("lodging", []))
    
    # Activities phase should use weather and places tools
    activity_tools = phase_tools.get("activities", [])
    assert any("weather" in tool for tool in activity_tools)
    assert any("places" in tool for tool in activity_tools)


def test_budget_allocation_logic(sample_user_request):
    """Test budget allocation calculations."""
    agent_state = create_plan(sample_user_request)
    
    allocations = agent_state.allocations
    assert allocations is not None
    
    # Transport allocation should be reasonable
    assert 0 < allocations.transport <= 100
    
    # Lodging should get majority of budget
    assert allocations.lodging_target > allocations.transport
    
    # Activities buffer should be at least $150
    assert allocations.activities_buffer >= 150
    
    # Total allocation should be reasonable relative to budget
    total_allocated = (
        allocations.transport + 
        allocations.lodging_target + 
        allocations.activities_buffer
    )
    assert total_allocated <= sample_user_request.budget_total * 1.2  # Allow some buffer


@patch('agent.planner.get_json_completion')
def test_create_plan_with_llm_mock(mock_llm, sample_user_request):
    """Test plan creation with mocked LLM response."""
    
    # Mock LLM response
    mock_response = {
        "steps": [
            {
                "phase": "transport",
                "description": "Find directions",
                "tool": "maps.find_directions",
                "params": {"origin": "Dallas, TX", "destination": "Austin, TX"}
            },
            {
                "phase": "lodging",
                "description": "Search hotels",
                "tool": "hotels.search",
                "params": {"city": "Austin, TX", "max_price": 200, "limit": 5}
            },
            {
                "phase": "synthesis",
                "description": "Create itinerary",
                "tool": "synthesis.none",
                "params": {}
            }
        ],
        "allocations": {
            "transport": 50.0,
            "lodging_target": 400.0,
            "activities_buffer": 350.0
        },
        "reasoning": "Test reasoning"
    }
    
    mock_llm.return_value = mock_response
    
    agent_state = create_plan(sample_user_request)
    
    # Verify LLM was called
    mock_llm.assert_called_once()
    
    # Verify structure
    assert len(agent_state.plan) == 3
    assert agent_state.plan[0].phase == "transport"
    assert agent_state.plan[1].phase == "lodging"
    assert agent_state.plan[2].phase == "synthesis"
    
    # Verify allocations
    assert agent_state.allocations.transport == 50.0
    assert agent_state.allocations.lodging_target == 400.0
    assert agent_state.allocations.activities_buffer == 350.0


def test_validate_plan_success(sample_user_request):
    """Test plan validation with valid plan."""
    agent_state = create_plan(sample_user_request)
    
    issues = validate_plan(agent_state)
    
    # Should have no major issues (empty list or minor warnings only)
    assert isinstance(issues, list)
    
    # Check that critical phases are present
    phases = {step.phase for step in agent_state.plan}
    required_phases = {"transport", "lodging", "activities", "synthesis"}
    assert required_phases.issubset(phases)


def test_validate_plan_missing_phases():
    """Test plan validation with missing phases."""
    from agent.state import AgentState
    
    # Create incomplete plan
    incomplete_plan = [
        PlanStep(phase="transport", description="Test", tool="maps.test", params={})
    ]
    
    agent_state = AgentState(
        budget_remaining=800.0,
        plan=incomplete_plan
    )
    
    issues = validate_plan(agent_state)
    
    # Should detect missing phases
    assert len(issues) > 0
    assert any("missing" in issue.lower() for issue in issues)


def test_estimate_plan_duration():
    """Test plan duration estimation."""
    plan_steps = [
        PlanStep(phase="transport", description="Test", tool="maps.find_directions", params={}),
        PlanStep(phase="lodging", description="Test", tool="hotels.search", params={}),
        PlanStep(phase="activities", description="Test", tool="places.search", params={}),
        PlanStep(phase="synthesis", description="Test", tool="synthesis.none", params={})
    ]
    
    duration = estimate_plan_duration(plan_steps)
    
    # Should return reasonable duration
    assert isinstance(duration, int)
    assert duration > 0
    assert duration < 60  # Less than 1 hour for basic plan


def test_create_plan_with_interests(sample_user_request):
    """Test that plan includes steps for user interests."""
    # Modify interests
    sample_user_request.interests = ["BBQ", "live music", "museums"]
    
    agent_state = create_plan(sample_user_request)
    
    # Check that activities phase has multiple steps
    activity_steps = [step for step in agent_state.plan if step.phase == "activities"]
    
    # Should have at least one step per interest plus weather
    assert len(activity_steps) >= 2  # At least weather + some activities
    
    # Check that tool parameters include interest queries
    activity_params = []
    for step in activity_steps:
        if step.tool == "places.search":
            activity_params.extend(step.params.values())
    
    # Should find at least some interest matches in parameters
    param_str = " ".join(str(p).lower() for p in activity_params)
    interest_matches = sum(1 for interest in sample_user_request.interests 
                          if interest.lower() in param_str)
    
    assert interest_matches > 0


def test_create_plan_budget_constraints():
    """Test plan creation with different budget constraints."""
    
    # Test low budget
    low_budget_request = UserRequest(
        origin="Dallas, TX",
        destination="Austin, TX", 
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=8),
        travelers=2,
        budget_total=300.0,  # Low budget
        interests=["BBQ"]
    )
    
    agent_state = create_plan(low_budget_request)
    
    # Should still create valid plan
    assert agent_state.budget_remaining == 300.0
    assert len(agent_state.plan) > 0
    
    # Budget allocations should be proportional
    assert agent_state.allocations.transport < 100
    assert agent_state.allocations.lodging_target < 200


def test_create_plan_single_day_trip():
    """Test plan creation for single day trip."""
    single_day_request = UserRequest(
        origin="Dallas, TX",
        destination="Austin, TX",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=7),  # Same day
        travelers=1,
        budget_total=500.0,
        interests=["BBQ"]
    )
    
    agent_state = create_plan(single_day_request)
    
    # Should handle single day trip
    assert agent_state is not None
    assert len(agent_state.plan) > 0
    
    # Budget allocations should be reasonable for day trip
    assert agent_state.allocations.lodging_target >= 0  # Might be 0 for day trip
    assert agent_state.allocations.activities_buffer > 0
