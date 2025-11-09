"""
Nemotron Itinerary Agent - Streamlit Application
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

# Import agent modules
from agent.state import UserRequest
from agent.planner import create_plan
from agent.executor import execute_plan, select_activities
from agent.synthesizer import create_itinerary, generate_calendar_events
from agent.llm import llm_client

# Page configuration
st.set_page_config(
    page_title="Nemotron Itinerary Agent",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .agent-log {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .tool-result {
        background-color: #ffffff;
        border-left: 4px solid #28a745;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .budget-box {
        background-color: #e8f4fd;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        text-align: center;
    }
    .itinerary-item {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    }
    .decision-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        margin: 0.25rem;
        display: inline-block;
    }
    /* Music button styling */
    a[data-testid="stLinkButton"] {
        text-decoration: none !important;
        color: white !important;
    }
    /* Color palette visibility */
    .color-swatch {
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        border: 4px solid !important;
    }
    /* Better contrast for badges */
    .genre-badge, .mood-badge, .use-badge {
        font-weight: bold !important;
        border: 2px solid !important;
        padding: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">🧳 Nemotron Itinerary Agent</div>', unsafe_allow_html=True)
    
    # Show Nemotron badge if API is configured
    if llm_client.has_api_config and not llm_client.use_mocks:
        st.success("🚀 Powered by Nemotron AI")
    elif not llm_client.use_mocks:
        st.info("🤖 Ready to connect to Nemotron (configure API keys)")
    else:
        st.info("🧪 Running in demo mode with mock data")
    
    # Sidebar for user input
    with st.sidebar:
        st.header("Trip Configuration")
        
        # Basic trip details
        origin = st.text_input("Origin", value="Dallas, TX", help="Starting location for your trip")
        destination = st.text_input("Destination", value="Austin, TX", help="Where you want to go")
        
        # Dates
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date", 
                value=date.today() + timedelta(days=7),
                min_value=date.today()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today() + timedelta(days=9),
                min_value=start_date
            )
        
        # Trip details
        travelers = st.number_input("Number of Travelers", min_value=1, max_value=10, value=2)
        budget = st.number_input("Total Budget ($)", min_value=100, max_value=10000, value=800, step=50)
        
        # Interests
        available_interests = ["BBQ", "live music", "parks", "museums", "coffee", "breweries", "outdoor activities", "nightlife", "art", "shopping"]
        interests = st.multiselect(
            "Interests", 
            available_interests,
            default=["BBQ", "live music"],
            help="Select activities and experiences you're interested in"
        )
        
        # Configuration options
        st.header("Configuration")
        use_mocks = st.checkbox("Use mock data", value=False, help="Use sample data for demo (faster, but uses fake data)")
        
        # Weather demo mode
        weather_mode = st.selectbox(
            "Weather Demo Mode",
            ["sunny", "rainy"],
            help="Toggle weather conditions for demo purposes"
        )
        
        # Set environment variable for weather demo
        os.environ["WEATHER_DEMO_MODE"] = weather_mode
        
        # Run button
        run_agent = st.button("🚀 Plan My Trip", type="primary", use_container_width=True)
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'user_request' not in st.session_state:
        st.session_state.user_request = None
    
    # Main content area
    if run_agent:
        # Validate inputs
        if not origin or not destination:
            st.error("Please provide both origin and destination")
        elif start_date >= end_date:
            st.error("End date must be after start date")
        else:
            if not interests:
                st.warning("Consider adding some interests for better recommendations")
            
            # Create user request
            user_request = UserRequest(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                travelers=travelers,
                budget_total=float(budget),
                interests=interests
            )
            
            # Update mock configuration
            os.environ["USE_MOCKS"] = str(use_mocks).lower()
            
            # Store in session state
            st.session_state.user_request = user_request
            
            # Run the agent
            run_itinerary_agent(user_request)
    
    # Display results from session state (persists across reruns)
    if st.session_state.results is not None and st.session_state.user_request is not None:
        # Add a "New Trip" button at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🆕 Plan New Trip", type="secondary", use_container_width=True):
                # Clear session state
                st.session_state.results = None
                st.session_state.user_request = None
                st.rerun()
        
        # Show trip summary
        st.markdown(f"""
        ### 🎯 **Your Trip: {st.session_state.user_request.origin} → {st.session_state.user_request.destination}**
        📅 **{st.session_state.user_request.start_date.strftime("%B %d")} - {st.session_state.user_request.end_date.strftime("%B %d, %Y")}** | 
        👥 **{st.session_state.user_request.travelers} travelers** | 
        💰 **${st.session_state.user_request.budget_total:.0f} budget** | 
        🎯 **{', '.join(st.session_state.user_request.interests[:3])}{'...' if len(st.session_state.user_request.interests) > 3 else ''}**
        """)
        
        st.markdown("---")  # Separator line
        
        display_results(
            st.session_state.results['agent_state'], 
            st.session_state.results['itinerary'], 
            st.session_state.user_request
        )
    
    else:
        # Show welcome message and instructions
        st.markdown("""
        ## Welcome to the Nemotron Itinerary Agent! 👋
        
        This AI agent will help you plan your perfect trip by:
        
        🗺️ **Planning** - Creating a multi-step execution plan
        🚗 **Transport** - Finding the best way to get there  
        🏨 **Lodging** - Selecting hotels within your budget
        🎯 **Activities** - Finding things to do based on your interests
        📊 **Budget Management** - Tracking costs and re-planning when needed
        
        ### How it works:
        1. Configure your trip details in the sidebar
        2. Click "Plan My Trip" to start the agent
        3. Watch the agent make decisions and adapt to constraints
        4. Get your personalized itinerary with budget breakdown and map
        
        ### Demo Features:
        - Toggle between sunny and rainy weather to see re-planning
        - Try different budget amounts to trigger "Plan B" hotel selection
        - Mix interests to see multi-interest venue matching
        
        **Ready to start planning?** Fill out the form on the left and click the button!
        """)


def run_itinerary_agent(user_request: UserRequest):
    """Run the complete itinerary agent workflow."""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Planning
        status_text.text("🧠 Creating execution plan...")
        progress_bar.progress(20)
        
        agent_state = create_plan(user_request)
        
        # Step 2: Execution
        status_text.text("⚡ Executing plan steps...")
        progress_bar.progress(40)
        
        agent_state = execute_plan(agent_state)
        
        # Step 3: Activity Selection
        status_text.text("🎯 Selecting activities...")
        progress_bar.progress(60)
        
        agent_state = select_activities(agent_state, user_request.interests, destination_city=user_request.destination)
        
        # Step 4: Synthesis
        status_text.text("📋 Creating itinerary...")
        progress_bar.progress(80)
        
        itinerary = create_itinerary(agent_state, user_request)
        
        status_text.text("✅ Complete!")
        progress_bar.progress(100)
        
        # Store results in session state (will persist across reruns)
        st.session_state.results = {
            'agent_state': agent_state,
            'itinerary': itinerary
        }
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Force a rerun to display results
        st.rerun()
        
    except Exception as e:
        error_msg = f"Agent execution failed: {str(e)}"
        st.error(error_msg)
        st.exception(e)
        
        # Show more details for debugging
        with st.expander("🔍 Debug Information", expanded=True):
            st.code(f"Error Type: {type(e).__name__}")
            st.code(f"Error Message: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
        
        # Clear session state on error
        st.session_state.results = None


def display_results(agent_state, itinerary, user_request):
    """Display the complete agent results."""
    
    # Check if we have any results to display
    if not agent_state.log:
        st.warning("⚠️ No execution log found. The agent may not have run successfully.")
        return
    
    if not itinerary.items:
        st.warning("⚠️ No itinerary items generated. This might indicate the agent didn't find any activities or there was an issue.")
    
    # Agent Log Section
    st.markdown('<div class="section-header">🤖 Agent Execution Log</div>', unsafe_allow_html=True)
    
    with st.expander("View Complete Agent Log", expanded=False):
        for i, tool_result in enumerate(agent_state.log):
            with st.container():
                # Show thinking if available
                thinking_section = ""
                if tool_result.thinking:
                    thinking_section = f'<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 0.75rem; margin: 0.5rem 0; border-radius: 0.25rem;"><strong>🤔 Agent Thinking:</strong><pre style="white-space: pre-wrap; font-size: 0.9em;">{tool_result.thinking}</pre></div>'
                
                st.markdown(f"""
                <div class="tool-result">
                    <strong>Step {i+1}: {tool_result.tool}</strong><br>
                    <em>Input:</em> {json.dumps(tool_result.input, indent=2)}<br>
                    <em>Cost:</em> ${tool_result.cost_estimate:.2f}<br>
                    <em>Notes:</em> {tool_result.notes}
                </div>
                {thinking_section}
                """, unsafe_allow_html=True)
    
    # Agent Decisions (Key highlights)
    if itinerary.agent_decisions:
        st.markdown("### 🎯 Key Agent Decisions")
        for decision in itinerary.agent_decisions:
            st.markdown(f'<div class="decision-badge">{decision}</div>', unsafe_allow_html=True)
    
    # Itinerary Section
    st.markdown('<div class="section-header">📋 Your Personalized Itinerary</div>', unsafe_allow_html=True)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Daily Schedule", "💰 Budget Breakdown", "🗺️ Map View", "👔 Clothing Suggestions", "🎵 Music for Social Media"])
    
    with tab1:
        display_daily_schedule(itinerary)
    
    with tab2:
        display_budget_breakdown(itinerary)
    
    with tab3:
        display_map(itinerary, user_request)
    
    with tab4:
        display_clothing_suggestions(itinerary)
    
    with tab5:
        display_music_recommendations(itinerary)
    
    # Download Options
    st.markdown('<div class="section-header">💾 Download Options</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        itinerary_dict = itinerary.model_dump() if hasattr(itinerary, 'model_dump') else itinerary.dict()
        itinerary_json = json.dumps(itinerary_dict, indent=2, default=str)
        st.download_button(
            label="📄 Download Itinerary JSON",
            data=itinerary_json,
            file_name=f"itinerary_{user_request.destination.replace(' ', '_')}_{user_request.start_date}.json",
            mime="application/json"
        )
    
    with col2:
        # Calendar events
        calendar_events = generate_calendar_events(itinerary)
        if calendar_events:
            calendar_data = json.dumps(calendar_events, indent=2)
            st.download_button(
                label="📅 Download Calendar Events",
                data=calendar_data,
                file_name=f"calendar_{user_request.destination.replace(' ', '_')}_{user_request.start_date}.json",
                mime="application/json"
            )


def display_daily_schedule(itinerary):
    """Display the daily schedule view."""
    
    if not itinerary.items:
        st.warning("⚠️ No schedule items available. The itinerary may still be processing.")
        return
    
    # Group items by day
    days = {}
    for item in itinerary.items:
        day_str = item.day.strftime("%B %d, %Y")
        if day_str not in days:
            days[day_str] = []
        days[day_str].append(item)
    
    # Sort days chronologically by the actual date
    sorted_days = sorted(days.items(), key=lambda x: next((item.day for item in x[1]), date.today()))
    
    for day, items in sorted_days:
        st.subheader(f"📅 {day}")
        
        for item in items:
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.write(f"**{item.time}**")
                
                with col2:
                    title = item.title
                    if item.link:
                        title = f"[{title}]({item.link})"
                    st.write(title)
                    
                    if item.address:
                        st.caption(f"📍 {item.address}")
                    
                    if item.notes:
                        st.caption(f"ℹ️ {item.notes}")
                
                with col3:
                    if item.est_cost > 0:
                        st.write(f"💰 ${item.est_cost:.2f}")
            
            st.divider()


def display_budget_breakdown(itinerary):
    """Display the budget breakdown view."""
    
    budget = itinerary.budget_breakdown
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚗 Transport", f"${budget.transport:.2f}")
    
    with col2:
        st.metric("🏨 Lodging", f"${budget.lodging:.2f}")
    
    with col3:
        st.metric("🎯 Activities", f"${budget.activities:.2f}")
    
    with col4:
        st.metric("💵 Remaining", f"${budget.remaining:.2f}")
    
    # Budget visualization
    st.subheader("Budget Allocation")
    
    budget_data = {
        "Category": ["Transport", "Lodging", "Activities", "Remaining"],
        "Amount": [budget.transport, budget.lodging, budget.activities, budget.remaining],
        "Percentage": [
            (budget.transport / budget.total_spent * 100) if budget.total_spent > 0 else 0,
            (budget.lodging / budget.total_spent * 100) if budget.total_spent > 0 else 0,
            (budget.activities / budget.total_spent * 100) if budget.total_spent > 0 else 0,
            (budget.remaining / (budget.total_spent + budget.remaining) * 100) if (budget.total_spent + budget.remaining) > 0 else 0
        ]
    }
    
    df = pd.DataFrame(budget_data)
    
    # Bar chart
    st.bar_chart(df.set_index("Category")["Amount"])
    
    # Detailed breakdown
    st.subheader("Detailed Breakdown")
    st.dataframe(df, use_container_width=True)
    
    # Budget utilization
    utilization = (budget.total_spent / (budget.total_spent + budget.remaining)) * 100 if (budget.total_spent + budget.remaining) > 0 else 0
    # Clamp progress value between 0.0 and 1.0 for Streamlit progress bar
    progress_value = min(1.0, max(0.0, utilization / 100))
    st.progress(progress_value)
    st.caption(f"Budget Utilization: {utilization:.1f}%")


def display_map(itinerary, user_request):
    """Display the map view with pins."""
    
    if not itinerary.map_points:
        st.warning("No map points available")
        return
    
    # Calculate center point
    center_lat = sum(point.lat for point in itinerary.map_points) / len(itinerary.map_points)
    center_lng = sum(point.lng for point in itinerary.map_points) / len(itinerary.map_points)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lng], zoom_start=12)
    
    # Add markers
    for point in itinerary.map_points:
        icon_color = "red" if point.type == "hotel" else "blue"
        icon = "home" if point.type == "hotel" else "star"
        
        popup_text = f"<b>{point.name}</b>"
        if point.link:
            popup_text += f'<br><a href="{point.link}" target="_blank">More Info</a>'
        
        folium.Marker(
            location=[point.lat, point.lng],
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=point.name,
            icon=folium.Icon(color=icon_color, icon=icon)
        ).add_to(m)
    
    # Display map
    st_data = st_folium(m, width=700, height=500)
    
    # Map legend
    st.markdown("""
    **Map Legend:**
    🏠 Red markers = Hotel
    ⭐ Blue markers = Activities
    """)
    
    # Map summary
    st.subheader("Map Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📍 Total Locations", len(itinerary.map_points))
    
    with col2:
        activity_count = len([p for p in itinerary.map_points if p.type == "activity"])
        st.metric("🎯 Activities", activity_count)


def display_clothing_suggestions(itinerary):
    """Display clothing suggestions based on weather and season."""
    
    if not itinerary.clothing_recommendations:
        st.info("👔 Clothing suggestions are being generated based on your trip dates and destination...")
        return
    
    rec = itinerary.clothing_recommendations
    
    # Weather summary
    season_display = ""
    if rec.seasons and len(rec.seasons) > 1:
        season_names = " & ".join([s.title() for s in rec.seasons])
        season_display = f" | **Seasons:** {season_names} (multi-season trip)"
    elif rec.season:
        season_display = f" | **Season:** {rec.season.title()}"
    
    climate_display = f" | **Climate:** {rec.climate_zone.replace('_', ' ').title()}" if rec.climate_zone else ""
    source_display = f" (based on {rec.weather_source.replace('_', ' ')})" if rec.weather_source else ""
    
    st.markdown(f"""
    ### 🌤️ Weather-Based Clothing Recommendations{source_display}
    
    **Weather:** {rec.weather_summary} | **Temperature:** {rec.temperature_range} | **Rain Chance:** {int(rec.rain_chance * 100)}%{season_display}{climate_display}
    """)
    
    # Display suggestions for each gender
    if rec.male_suggestions:
        st.markdown("---")
        st.subheader("👔 Male Clothing Suggestions")
        _display_gender_suggestions(rec.male_suggestions)
    
    if rec.female_suggestions:
        st.markdown("---")
        st.subheader("👗 Female Clothing Suggestions")
        _display_gender_suggestions(rec.female_suggestions)


def _display_gender_suggestions(suggestions):
    """Display clothing suggestions for a specific gender."""
    
    # Color Palette with better visibility and contrast
    st.markdown("#### 🎨 Color Palette")
    if suggestions.color_palette:
        # Use a grid layout for better display
        num_colors = len(suggestions.color_palette)
        cols = st.columns(num_colors if num_colors <= 6 else 6)
        
        for i, color in enumerate(suggestions.color_palette):
            col_idx = i % 6 if num_colors > 6 else i
            with cols[col_idx]:
                # Determine text color for better contrast
                text_color = "white" if _is_dark_color(color.hex) else "black"
                # Use a darker border for better visibility
                border_color = "#000000" if _is_dark_color(color.hex) else "#333333"
                
                # Color swatch with better visibility
                st.markdown(
                    f'<div style="background-color: {color.hex}; height: 100px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: {text_color}; font-weight: bold; border: 4px solid {border_color}; box-shadow: 0 4px 8px rgba(0,0,0,0.3); margin-bottom: 0.75rem; font-size: 1.1em; text-shadow: {"2px 2px 4px rgba(0,0,0,0.8)" if not _is_dark_color(color.hex) else "none"};">{color.name}</div>',
                    unsafe_allow_html=True
                )
                # Hex code display with better contrast
                st.markdown(
                    f'<div style="background-color: #ffffff; padding: 0.5rem; border-radius: 0.5rem; text-align: center; font-family: monospace; font-size: 0.9em; color: #212121; border: 2px solid #e0e0e0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{color.hex}</div>',
                    unsafe_allow_html=True
                )
        
        # Add new row if more than 6 colors
        if num_colors > 6:
            cols2 = st.columns(num_colors - 6)
            for i, color in enumerate(suggestions.color_palette[6:], 6):
                col_idx = i - 6
                with cols2[col_idx]:
                    text_color = "white" if _is_dark_color(color.hex) else "black"
                    border_color = "#000000" if _is_dark_color(color.hex) else "#333333"
                    st.markdown(
                        f'<div style="background-color: {color.hex}; height: 100px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: {text_color}; font-weight: bold; border: 4px solid {border_color}; box-shadow: 0 4px 8px rgba(0,0,0,0.3); margin-bottom: 0.75rem; font-size: 1.1em; text-shadow: {"2px 2px 4px rgba(0,0,0,0.8)" if not _is_dark_color(color.hex) else "none"};">{color.name}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<div style="background-color: #ffffff; padding: 0.5rem; border-radius: 0.5rem; text-align: center; font-family: monospace; font-size: 0.9em; color: #212121; border: 2px solid #e0e0e0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{color.hex}</div>',
                        unsafe_allow_html=True
                    )
    
    # Outfit Items
    st.markdown("#### 👕 Recommended Outfit Items")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if suggestions.outfit_items.tops:
            st.markdown("**Tops:**")
            for item in suggestions.outfit_items.tops:
                st.markdown(f"- {item}")
        
        if suggestions.outfit_items.bottoms:
            st.markdown("**Bottoms:**")
            for item in suggestions.outfit_items.bottoms:
                st.markdown(f"- {item}")
        
        if suggestions.outfit_items.outerwear:
            st.markdown("**Outerwear:**")
            for item in suggestions.outfit_items.outerwear:
                st.markdown(f"- {item}")
    
    with col2:
        if suggestions.outfit_items.footwear:
            st.markdown("**Footwear:**")
            for item in suggestions.outfit_items.footwear:
                st.markdown(f"- {item}")
        
        if suggestions.outfit_items.accessories:
            st.markdown("**Accessories:**")
            for item in suggestions.outfit_items.accessories:
                st.markdown(f"- {item}")
        
        if suggestions.special_items:
            st.markdown("**Special Items:**")
            for item in suggestions.special_items:
                st.markdown(f"- {item}")
    
    # Style Notes
    if suggestions.style_notes:
        st.markdown("#### 💡 Style Notes")
        st.info(suggestions.style_notes)


def _is_dark_color(hex_color: str) -> bool:
    """Check if a color is dark (for text contrast)."""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Calculate luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        return luminance < 0.5
    except:
        return False


def display_music_recommendations(itinerary):
    """Display music recommendations for social media based on location."""
    
    if not itinerary.music_recommendations:
        st.info("🎵 Music recommendations are being generated based on your destination...")
        return
    
    music_rec = itinerary.music_recommendations
    
    # Header with better styling
    st.markdown(f"""
    <div style="background-color: #ffffff; padding: 1.5rem; border-radius: 0.5rem; border: 2px solid #e0e0e0; margin-bottom: 1.5rem;">
        <h2 style="color: #1f77b4; margin-bottom: 0.5rem;">🎵 Music Recommendations for {music_rec.destination}</h2>
        <p style="color: #333333; font-size: 1.1em; margin: 0.5rem 0;">
            <strong style="color: #2c3e50;">Popular Genres:</strong> <span style="color: #555555;">{', '.join(music_rec.location_genres) if music_rec.location_genres else 'Various'}</span> | 
            <strong style="color: #2c3e50;">Season:</strong> <span style="color: #555555;">{music_rec.season.title() if music_rec.season else 'Any'}</span> | 
            <strong style="color: #2c3e50;">Mood:</strong> <span style="color: #555555;">{music_rec.mood.title()}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2196F3; margin: 1rem 0;">
        <strong style="color: #1565C0;">💡 Perfect for:</strong> <span style="color: #424242;">Instagram Stories, TikTok, Reels, Photo Slideshows, and other social media posts!</span>
        <br>
        <span style="color: #616161;">These songs are curated based on your destination and are perfect for showcasing your trip.</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display songs
    if music_rec.songs:
        st.markdown("#### 🎶 Recommended Songs")
        
        for i, song in enumerate(music_rec.songs, 1):
            # Song card with better styling
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 0.5rem; padding: 1.25rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #1f77b4; margin-bottom: 0.5rem; font-size: 1.2em;">{i}. {song.title}</h3>
                <p style="color: #666666; font-style: italic; margin-bottom: 0.75rem; font-size: 1em;">by <strong style="color: #424242;">{song.artist}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Genre, mood, and use case badges with better contrast
            col_genre, col_mood, col_use = st.columns(3)
            with col_genre:
                st.markdown(f'<div style="background-color: #e3f2fd; color: #1565C0; padding: 0.5rem; border-radius: 0.5rem; text-align: center; font-weight: bold; border: 2px solid #90caf9;">🎸 {song.genre}</div>', unsafe_allow_html=True)
            with col_mood:
                st.markdown(f'<div style="background-color: #f3e5f5; color: #7b1fa2; padding: 0.5rem; border-radius: 0.5rem; text-align: center; font-weight: bold; border: 2px solid #ce93d8;">✨ {song.mood}</div>', unsafe_allow_html=True)
            with col_use:
                st.markdown(f'<div style="background-color: #e8f5e9; color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; text-align: center; font-weight: bold; border: 2px solid #a5d6a7;">📱 {song.best_for}</div>', unsafe_allow_html=True)
            
            if song.why:
                st.markdown(f'<p style="color: #424242; font-size: 0.95em; margin-top: 0.75rem; padding: 0.75rem; background-color: #fafafa; border-radius: 0.25rem; border-left: 3px solid #ff9800;">💭 <em>{song.why}</em></p>', unsafe_allow_html=True)
            
            # Action buttons - using styled HTML links that look like proper buttons
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            
            search_query = f"{song.artist} {song.title}"
            spotify_url = f"https://open.spotify.com/search/{search_query.replace(' ', '%20')}"
            youtube_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            with col_btn1:
                # Spotify button - styled as a prominent button
                st.markdown(f"""
                <a href="{spotify_url}" target="_blank" style="
                    display: block;
                    background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
                    color: white !important;
                    text-decoration: none !important;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(29, 185, 84, 0.4);
                    border: 2px solid #1DB954;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    margin: 8px 0;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(29, 185, 84, 0.5)';" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(29, 185, 84, 0.4)';">
                    🎵 Listen on Spotify
                </a>
                """, unsafe_allow_html=True)
            
            with col_btn2:
                # YouTube button - styled as a prominent button
                st.markdown(f"""
                <a href="{youtube_url}" target="_blank" style="
                    display: block;
                    background: linear-gradient(135deg, #FF0000 0%, #ff3333 100%);
                    color: white !important;
                    text-decoration: none !important;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(255, 0, 0, 0.4);
                    border: 2px solid #FF0000;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    margin: 8px 0;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(255, 0, 0, 0.5)';" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(255, 0, 0, 0.4)';">
                    ▶️ Watch on YouTube
                </a>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Summary with better styling
        st.markdown("---")
        st.markdown("#### 📊 Summary")
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 2px solid #90caf9;">
                <div style="font-size: 2em; font-weight: bold; color: #1565C0;">{len(music_rec.songs)}</div>
                <div style="color: #424242; font-weight: bold;">🎵 Total Songs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with summary_col2:
            unique_genres = len(set(song.genre for song in music_rec.songs))
            st.markdown(f"""
            <div style="background-color: #f3e5f5; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 2px solid #ce93d8;">
                <div style="font-size: 2em; font-weight: bold; color: #7b1fa2;">{unique_genres}</div>
                <div style="color: #424242; font-weight: bold;">🎸 Genres</div>
            </div>
            """, unsafe_allow_html=True)
        
        with summary_col3:
            moods = set(song.mood for song in music_rec.songs)
            st.markdown(f"""
            <div style="background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 2px solid #a5d6a7;">
                <div style="font-size: 2em; font-weight: bold; color: #2e7d32;">{len(moods)}</div>
                <div style="color: #424242; font-weight: bold;">✨ Moods</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Genre breakdown with better styling
        if music_rec.songs:
            st.markdown("#### 🎸 Genre Breakdown")
            genre_counts = {}
            for song in music_rec.songs:
                genre_counts[song.genre] = genre_counts.get(song.genre, 0) + 1
            
            genre_html = '<div style="background-color: #fafafa; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e0e0e0;">'
            for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
                genre_html += f'<span style="display: inline-block; background-color: #e3f2fd; color: #1565C0; padding: 0.5rem 1rem; margin: 0.25rem; border-radius: 0.5rem; font-weight: bold; border: 2px solid #90caf9;"><strong>{genre}</strong>: {count}</span>'
            genre_html += '</div>'
            st.markdown(genre_html, unsafe_allow_html=True)
    else:
        st.warning("No songs found. Please try again or check your destination.")


if __name__ == "__main__":
    main()
