# API Mode Configuration - Changes Made

## ✅ All Changes Complete

The agent has been configured to use **real APIs by default** instead of mock/demo mode.

## Changes Made

### 1. Default Configuration Updated
Changed all default `USE_MOCKS` settings from `"true"` to `"false"`:

- ✅ `agent/llm.py` - LLM client now defaults to API mode
- ✅ `tools/maps.py` - Maps tool defaults to Google Maps API
- ✅ `tools/weather.py` - Weather tool defaults to OpenWeather API
- ✅ `tools/places.py` - Places tool defaults to Google Places API
- ✅ `tools/hotels.py` - Hotels tool defaults to API mode
- ✅ `run.py` - Startup script defaults to API mode
- ✅ `app.py` - UI checkbox defaults to unchecked (API mode)

### 2. Environment Configuration
- ✅ `env.example` - Already has `USE_MOCKS=False`
- ✅ Your `.env` file - Already configured with `USE_MOCKS=false`

## How It Works Now

### Default Behavior
- **Without `.env` file**: Uses API mode (falls back to mocks only if API keys are missing)
- **With `.env` file**: Uses the `USE_MOCKS` setting from your `.env` file
- **In Streamlit UI**: Checkbox defaults to unchecked (API mode)

### API Requirements

For full API functionality, ensure your `.env` file has:

```bash
USE_MOCKS=false

# Nemotron LLM
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=your_nemotron_api_key
LLM_MODEL=nvidia/nvidia-nemotron-nano-9b-v2

# Google Maps (for directions and places)
GOOGLE_MAPS_API_KEY=your_google_maps_key

# OpenWeather (for weather forecasts)
OPENWEATHER_API_KEY=your_openweather_key
```

### Fallback Behavior

The agent will automatically fall back to mock data if:
1. `USE_MOCKS=true` is explicitly set
2. Required API keys are missing
3. API calls fail (with error logging)

## Testing

To verify API mode is working:

```bash
# Check your configuration
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('USE_MOCKS:', os.getenv('USE_MOCKS')); print('Has LLM Key:', bool(os.getenv('LLM_API_KEY')))"

# Run the app
streamlit run app.py
```

In the Streamlit UI, you should see:
- "🚀 Powered by Nemotron AI" (if API keys are configured)
- Real data from APIs instead of mock data

## Switching Back to Mock Mode

If you want to use mock mode temporarily:
1. Check the "Use mock data" checkbox in the Streamlit UI, OR
2. Set `USE_MOCKS=true` in your `.env` file

## Notes

- The agent will log API errors and automatically fall back to mocks if APIs fail
- All API calls have timeout protection (30 seconds for LLM, 10 seconds for others)
- The code handles both OpenAI-compatible endpoint formats automatically

