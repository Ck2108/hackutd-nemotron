# 🧳 Nemotron Itinerary Agent

An autonomous AI agent that plans complete trip itineraries using natural language processing, multi-step reasoning, and adaptive re-planning. Built for the 24-hour hackathon challenge with Nemotron LLM integration.

## 🎯 What Makes This Special

Unlike simple chatbots, this is a **true autonomous agent** that:

- 🧠 **Plans** multi-step execution workflows
- ⚡ **Executes** tool calls and tracks budget state  
- 🔄 **Re-plans** when constraints break (budget/weather/location)
- 📊 **Logs** all decisions with transparent reasoning
- 🗺️ **Synthesizes** complete itineraries with maps and schedules

## 🚀 Quick Start

### Option 1: Demo Mode (No Setup Required)
```bash
# Clone and run immediately with mock data
git clone <your-repo>
cd itinerary-agent
pip install -r requirements.txt
streamlit run app.py
```

### Option 2: With Nemotron AI
```bash
# 1. Copy environment template
cp env.example .env

# 2. Add your Nemotron API credentials to .env
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=your_nvidia_nim_api_key_here
LLM_MODEL=nvidia/nemotron-4-340b-reward
USE_MOCKS=false

# 3. Run the app
streamlit run app.py
```

## 🏗️ Architecture

### Agent Workflow
```
User Request → Planner → Executor → Synthesizer → Itinerary
     ↓           ↓         ↓          ↓           ↓
   Parse → Create Plan → Execute → Re-plan → Output
```

### Core Components

- **`agent/state.py`**: Pydantic models for all data structures
- **`agent/llm.py`**: Nemotron client with robust fallbacks  
- **`agent/planner.py`**: Creates ordered execution plans with budget allocation
- **`agent/executor.py`**: Runs tools, tracks budget, handles re-planning
- **`agent/synthesizer.py`**: Generates final itinerary with maps and schedules
- **`tools/`**: API wrappers for maps, weather, places, hotels (with mocks)

## 🎮 Demo Features

### Budget Re-planning
Set budget to **$500** to trigger Plan B hotel selection:
- Agent finds expensive hotels first
- Detects budget constraint 
- Automatically searches for cheaper options
- Logs the decision process

### Weather Adaptation  
Toggle weather to **"rainy"** in the sidebar:
- Agent checks forecast
- Detects rain >50% chance
- Swaps outdoor activities for indoor alternatives
- Shows weather re-planning in agent log

### Multi-Interest Matching
Select **"BBQ"** and **"live music"**:
- Agent finds Stubb's Bar-B-Q (satisfies both interests)
- Prioritizes venues that match multiple preferences
- Optimizes activity selection

## 📊 Agent Decision Log

The app shows complete transparency with:

```
🤖 Agent Execution Log
├── Step 1: maps.find_directions
│   ├── Input: {"origin": "Dallas, TX", "destination": "Austin, TX"}
│   ├── Cost: $27.30
│   └── Notes: Driving route: 195 miles, 195 min, $27.30 gas
├── Step 2: hotels.search  
│   ├── Input: {"city": "Austin, TX", "max_price": 200}
│   ├── Cost: $240.00
│   └── Notes: Hotel selected: Hampton Inn - $240.00 total
└── Step 3: activities.select
    ├── Cost: $67.00
    └── Notes: Selected 4 activities (including 1 multi-interest match)
```

## 🗺️ Output Features

### 📅 Daily Schedule
- Morning/Afternoon/Evening time blocks
- Activities with ratings, costs, and links
- Hotel check-in/check-out handling

### 💰 Budget Breakdown
- Transport, lodging, activities breakdown
- Visual budget utilization chart
- Remaining budget tracking

### 🗺️ Interactive Map
- Hotel pins (red) and activity pins (blue)
- Clickable markers with info and links
- Geographic optimization visualization

### 💾 Export Options
- **JSON**: Complete itinerary data
- **Calendar Events**: Import into Google Calendar/Outlook

## 🔧 Configuration

### Environment Variables

```bash
# Nemotron LLM Configuration
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=your_nvidia_nim_api_key_here  
LLM_MODEL=nvidia/nemotron-4-340b-reward
LLM_PROVIDER=openai_compatible

# Mock Data (default: true for demo)
USE_MOCKS=true

# Demo Controls
WEATHER_DEMO_MODE=sunny  # or "rainy"
```

### Mock Data Location
- `data/mock/places_austin.json` - Austin venues with overlapping interests
- `data/mock/hotels_austin.json` - Hotels at various price points  
- `data/mock/weather_next_weekend.json` - Sunny/rainy weather patterns

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_planner.py
pytest tests/test_executor.py

# Run with coverage
pytest --cov=agent tests/
```

### Test Coverage
- **Planner**: Plan structure, tool assignment, budget allocation, LLM integration
- **Executor**: Tool execution, budget tracking, constraint detection, re-planning
- **Mock Integration**: Deterministic fallbacks, constraint triggering

## 🎯 Demo Script

### 1. Default Success Case
- **Route**: Dallas → Austin  
- **Budget**: $800
- **Interests**: BBQ + Live Music
- **Expected**: Driving, mid-range hotel, Stubb's Bar-B-Q (multi-interest match)

### 2. Budget Constraint Demo
- **Budget**: $500
- **Expected**: Plan B hotel triggered, agent log shows downgrade decision

### 3. Weather Re-planning Demo  
- **Weather**: Toggle to "rainy"
- **Expected**: Indoor activities prioritized, weather re-plan logged

### 4. Geographic Optimization
- **Result**: Activities clustered near hotel, travel time minimized

## 🚀 Production Deployment

### Streamlit Cloud
```bash
# Push to GitHub, then deploy via Streamlit Cloud
# Add secrets in Streamlit Cloud dashboard:
LLM_API_KEY = "your_key"
LLM_API_BASE = "your_endpoint"
```

### Docker
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 🛠️ Development

### Adding New Tools
1. Create tool in `tools/new_tool.py`
2. Add mock data in `data/mock/`
3. Update executor to handle new tool calls
4. Add tests for the tool

### Adding New Constraints
1. Update `executor.py` constraint checking
2. Add re-planning logic in `planner.py`  
3. Test constraint triggering

### Extending LLM Integration
1. Modify `agent/llm.py` for new providers
2. Update schema handling for structured outputs
3. Maintain fallback compatibility

## 📈 Architecture Decisions

### Why Pydantic?
- Type safety for complex state management
- JSON schema generation for LLM structured outputs
- Validation and serialization built-in

### Why Streamlit?
- Rapid prototyping for hackathon timeline
- Built-in interactivity and visualization
- Easy deployment and sharing

### Why Mock-First?
- Reliable demos without API dependencies
- Faster development and testing
- Deterministic behavior for presentations

## 🎉 Demo Highlights

**"This isn't just a trip planner - it's an autonomous agent!"**

1. **🧠 Shows Reasoning**: Complete decision log with cost tracking
2. **🔄 Adapts to Constraints**: Budget and weather re-planning  
3. **🎯 Optimizes Choices**: Multi-interest matching, location clustering
4. **📊 Transparent Process**: Every tool call and decision logged
5. **🗺️ Visual Output**: Interactive maps with optimized routes

## 🏆 Hackathon Success Criteria

✅ **Autonomous Agent** (not chatbot) - Multi-step reasoning with state management  
✅ **Nemotron Integration** - LLM-powered planning with structured outputs  
✅ **Constraint Handling** - Budget/weather/geo re-planning with logging  
✅ **Complete Demo** - End-to-end workflow with visual outputs  
✅ **Production Ready** - Tests, documentation, deployment instructions  

---

**Built with ❤️ for the Nemotron Hackathon Challenge**

*"An agent that doesn't just chat about travel - it actually plans your trip."*
