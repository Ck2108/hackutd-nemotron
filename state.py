"""
Pydantic models for the Nemotron Itinerary Agent state management.
"""
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """User's trip request with all parameters."""
    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Destination location")
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    travelers: int = Field(default=2, description="Number of travelers")
    budget_total: float = Field(..., description="Total budget in USD")
    interests: List[str] = Field(default_factory=list, description="List of interests/activities")


class PlanStep(BaseModel):
    """Individual step in the agent's execution plan."""
    phase: Literal["transport", "lodging", "activities", "synthesis"] = Field(..., description="Execution phase")
    description: str = Field(..., description="Human-readable step description")
    tool: str = Field(..., description="Tool function to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool call")


class ToolResult(BaseModel):
    """Result of a tool execution."""
    tool: str = Field(..., description="Tool that was called")
    input: Dict[str, Any] = Field(..., description="Input parameters to the tool")
    output: Dict[str, Any] = Field(..., description="Raw output from the tool")
    cost_estimate: float = Field(default=0.0, description="Estimated cost impact in USD")
    notes: str = Field(default="", description="Human-readable notes about the result")
    thinking: str = Field(default="", description="Agent's reasoning/thinking process for this step")


class TransportSelection(BaseModel):
    """Selected transport option."""
    mode: str = Field(..., description="Transport mode (driving, flying, etc)")
    duration_minutes: int = Field(..., description="Travel time in minutes")
    distance_miles: float = Field(..., description="Distance in miles")
    cost: float = Field(..., description="Transport cost in USD")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional transport details")


class HotelSelection(BaseModel):
    """Selected hotel option."""
    name: str = Field(..., description="Hotel name")
    price_per_night: float = Field(..., description="Price per night in USD")
    total_price: float = Field(..., description="Total price for the stay")
    rating: float = Field(..., description="Hotel rating")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    link: Optional[str] = Field(None, description="Booking or info link")
    address: Optional[str] = Field(None, description="Hotel address")


class ActivitySelection(BaseModel):
    """Selected activity/place."""
    name: str = Field(..., description="Activity/place name")
    tags: List[str] = Field(default_factory=list, description="Activity tags/categories")
    rating: float = Field(..., description="Rating")
    price: float = Field(default=0.0, description="Estimated cost per person")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    place_id: Optional[str] = Field(None, description="Unique place identifier")
    link: Optional[str] = Field(None, description="Website or info link")
    address: Optional[str] = Field(None, description="Address")


class Selection(BaseModel):
    """All agent selections."""
    transport: Optional[TransportSelection] = None
    hotel: Optional[HotelSelection] = None
    activities: List[ActivitySelection] = Field(default_factory=list)


class BudgetAllocation(BaseModel):
    """Budget allocation hints for planning."""
    transport: float = Field(..., description="Estimated transport cost")
    lodging_target: float = Field(..., description="Target lodging budget")
    activities_buffer: float = Field(..., description="Activities budget buffer")


class AgentState(BaseModel):
    """Complete agent state during execution."""
    budget_remaining: float = Field(..., description="Remaining budget in USD")
    plan: List[PlanStep] = Field(default_factory=list, description="Execution plan steps")
    selections: Selection = Field(default_factory=Selection, description="Selected options")
    log: List[ToolResult] = Field(default_factory=list, description="Execution log")
    allocations: Optional[BudgetAllocation] = None


class ItineraryItem(BaseModel):
    """Single item in the itinerary."""
    day: date = Field(..., description="Date of the activity")
    time: str = Field(..., description="Time slot (e.g., 'Morning 9-12')")
    title: str = Field(..., description="Activity title")
    place_id: Optional[str] = Field(None, description="Place identifier")
    address: Optional[str] = Field(None, description="Address")
    link: Optional[str] = Field(None, description="Website or booking link")
    est_cost: float = Field(default=0.0, description="Estimated cost per person")
    notes: Optional[str] = Field(None, description="Additional notes")


class BudgetBreakdown(BaseModel):
    """Budget breakdown by category."""
    transport: float = Field(default=0.0, description="Transport costs")
    lodging: float = Field(default=0.0, description="Lodging costs")
    activities: float = Field(default=0.0, description="Activities costs")
    total_spent: float = Field(default=0.0, description="Total spent")
    remaining: float = Field(default=0.0, description="Remaining budget")


class MapPoint(BaseModel):
    """Point to show on the map."""
    name: str = Field(..., description="Location name")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    link: Optional[str] = Field(None, description="Website or info link")
    type: str = Field(default="activity", description="Point type (hotel, activity, etc)")


class ColorPalette(BaseModel):
    """Color in the palette."""
    name: str = Field(..., description="Color name")
    hex: str = Field(..., description="Hex color code")


class OutfitItems(BaseModel):
    """Outfit items by category."""
    tops: List[str] = Field(default_factory=list, description="Top clothing items")
    bottoms: List[str] = Field(default_factory=list, description="Bottom clothing items")
    outerwear: List[str] = Field(default_factory=list, description="Outerwear items")
    footwear: List[str] = Field(default_factory=list, description="Footwear items")
    accessories: List[str] = Field(default_factory=list, description="Accessories")


class ClothingSuggestion(BaseModel):
    """Clothing suggestions for a specific gender."""
    outfit_items: OutfitItems = Field(..., description="Recommended outfit items")
    color_palette: List[ColorPalette] = Field(default_factory=list, description="Recommended color palette")
    style_notes: str = Field(default="", description="Style and fashion notes")
    special_items: List[str] = Field(default_factory=list, description="Special items needed (umbrella, etc.)")


class ClothingRecommendations(BaseModel):
    """Complete clothing recommendations based on weather and season."""
    weather_summary: str = Field(..., description="Weather summary")
    temperature_range: str = Field(..., description="Temperature range")
    rain_chance: float = Field(..., description="Rain chance (0-1)")
    season: Optional[str] = Field(None, description="Primary season (spring, summer, fall, winter)")
    seasons: List[str] = Field(default_factory=list, description="All seasons covered by the trip")
    climate_zone: Optional[str] = Field(None, description="Climate zone of destination (west_coast, southern, northern, etc.)")
    weather_source: Optional[str] = Field(None, description="Source of weather data (weather_api, season, fallback)")
    male_suggestions: Optional[ClothingSuggestion] = Field(None, description="Clothing suggestions for males")
    female_suggestions: Optional[ClothingSuggestion] = Field(None, description="Clothing suggestions for females")


class SongRecommendation(BaseModel):
    """Individual song recommendation."""
    title: str = Field(..., description="Song title")
    artist: str = Field(..., description="Artist name")
    genre: str = Field(..., description="Music genre")
    mood: str = Field(..., description="Mood/energy level")
    why: str = Field(default="", description="Why this song fits the location")
    best_for: str = Field(default="Social Media", description="Best use case (Instagram, TikTok, etc.)")


class MusicRecommendations(BaseModel):
    """Music recommendations for social media based on location."""
    destination: str = Field(..., description="Destination location")
    location_genres: List[str] = Field(default_factory=list, description="Popular genres in the location")
    season: Optional[str] = Field(None, description="Season")
    mood: str = Field(default="vibrant", description="Overall mood")
    songs: List[SongRecommendation] = Field(default_factory=list, description="Recommended songs")


class CityHistory(BaseModel):
    """City history information."""
    destination: str = Field(..., description="Destination city name")
    history: str = Field(..., description="Brief history of the city")
    source: str = Field(default="gemini_api", description="Source of the history (gemini_api, mock, etc.)")
    length: int = Field(default=0, description="Length of history text in characters")


class Itinerary(BaseModel):
    """Complete itinerary output."""
    items: List[ItineraryItem] = Field(default_factory=list, description="Itinerary items")
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown, description="Budget summary")
    map_points: List[MapPoint] = Field(default_factory=list, description="Map pins")
    rationales: List[str] = Field(default_factory=list, description="Decision rationales")
    agent_decisions: List[str] = Field(default_factory=list, description="Key agent decisions made")
    clothing_recommendations: Optional[ClothingRecommendations] = Field(None, description="Clothing recommendations based on weather")
    music_recommendations: Optional[MusicRecommendations] = Field(None, description="Music recommendations for social media based on location")
    city_history: Optional[CityHistory] = Field(None, description="Brief history of the destination city")


class PlanningResponse(BaseModel):
    """Response from the planning phase."""
    steps: List[PlanStep] = Field(..., description="Ordered execution steps")
    allocations: BudgetAllocation = Field(..., description="Budget allocation hints")
    reasoning: str = Field(default="", description="Planning reasoning")
