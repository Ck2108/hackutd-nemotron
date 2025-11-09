#!/usr/bin/env python3
"""
Test script to verify the itinerary agent workflow runs properly.
"""
import os
import sys
from datetime import date, timedelta

# Set mock mode for testing
os.environ["USE_MOCKS"] = "true"
os.environ["WEATHER_DEMO_MODE"] = "sunny"

# Import agent modules
from agent.state import UserRequest
from agent.planner import create_plan
from agent.executor import execute_plan, select_activities
from agent.synthesizer import create_itinerary

def test_agent_workflow():
    """Test the complete agent workflow."""
    print("🧳 Testing Itinerary Agent Workflow")
    print("=" * 50)
    
    # Create a test user request
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    user_request = UserRequest(
        origin="Dallas, TX",
        destination="Austin, TX",
        start_date=start_date,
        end_date=end_date,
        travelers=2,
        budget_total=800.0,
        interests=["BBQ", "live music"]
    )
    
    print(f"\n📋 User Request:")
    print(f"   Origin: {user_request.origin}")
    print(f"   Destination: {user_request.destination}")
    print(f"   Dates: {user_request.start_date} to {user_request.end_date}")
    print(f"   Budget: ${user_request.budget_total}")
    print(f"   Interests: {', '.join(user_request.interests)}")
    
    try:
        # Step 1: Planning
        print("\n🧠 Step 1: Creating execution plan...")
        agent_state = create_plan(user_request)
        print(f"   ✅ Created plan with {len(agent_state.plan)} steps")
        print(f"   Budget remaining: ${agent_state.budget_remaining:.2f}")
        
        # Step 2: Execution
        print("\n⚡ Step 2: Executing plan...")
        agent_state = execute_plan(agent_state)
        print(f"   ✅ Executed {len(agent_state.log)} tool calls")
        print(f"   Budget remaining: ${agent_state.budget_remaining:.2f}")
        
        # Step 3: Activity Selection
        print("\n🎯 Step 3: Selecting activities...")
        agent_state = select_activities(agent_state, user_request.interests)
        print(f"   ✅ Selected {len(agent_state.selections.activities)} activities")
        print(f"   Budget remaining: ${agent_state.budget_remaining:.2f}")
        
        # Step 4: Synthesis
        print("\n📋 Step 4: Creating itinerary...")
        itinerary = create_itinerary(agent_state, user_request)
        print(f"   ✅ Created itinerary with {len(itinerary.items)} items")
        print(f"   Map points: {len(itinerary.map_points)}")
        print(f"   Agent decisions: {len(itinerary.agent_decisions)}")
        
        # Display summary
        print("\n" + "=" * 50)
        print("✅ AGENT WORKFLOW TEST PASSED")
        print("=" * 50)
        
        print(f"\n📊 Summary:")
        print(f"   Transport: ${itinerary.budget_breakdown.transport:.2f}")
        print(f"   Lodging: ${itinerary.budget_breakdown.lodging:.2f}")
        print(f"   Activities: ${itinerary.budget_breakdown.activities:.2f}")
        print(f"   Total Spent: ${itinerary.budget_breakdown.total_spent:.2f}")
        print(f"   Remaining: ${itinerary.budget_breakdown.remaining:.2f}")
        
        if agent_state.selections.transport:
            print(f"\n🚗 Transport: {agent_state.selections.transport.mode}")
            print(f"   Duration: {agent_state.selections.transport.duration_minutes} minutes")
            print(f"   Cost: ${agent_state.selections.transport.cost:.2f}")
        
        if agent_state.selections.hotel:
            print(f"\n🏨 Hotel: {agent_state.selections.hotel.name}")
            print(f"   Price: ${agent_state.selections.hotel.price_per_night:.2f}/night")
            print(f"   Total: ${agent_state.selections.hotel.total_price:.2f}")
        
        if agent_state.selections.activities:
            print(f"\n🎯 Activities ({len(agent_state.selections.activities)}):")
            for i, activity in enumerate(agent_state.selections.activities[:5], 1):
                print(f"   {i}. {activity.name} (${activity.price:.2f})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_workflow()
    sys.exit(0 if success else 1)

