# API Usage - Current Status

## ✅ Production Code Uses Real APIs

The production code **DOES use real APIs** when:
- `USE_MOCKS=false` (which is the default now)
- API keys are configured in `.env`

## Current API Behavior

### ✅ Maps API (Google Maps Directions)
- **Uses API**: When `USE_MOCKS=false` and `GOOGLE_MAPS_API_KEY` is set
- **Falls back**: Only on API errors (returns error status, not mock data)
- **Status**: ✅ Working with real API

### ✅ Places API (Google Places)
- **Uses API**: When `USE_MOCKS=false` and `GOOGLE_MAPS_API_KEY` is set
- **Falls back**: Returns empty list if API fails (no mock data)
- **Note**: Requires "Places API" (not legacy) enabled in Google Cloud Console
- **Status**: ✅ Uses API, returns empty if denied

### ✅ Weather API (OpenWeather)
- **Uses API**: When `USE_MOCKS=false` and `OPENWEATHER_API_KEY` is set
- **Falls back**: Returns error status if API fails (no mock data)
- **Status**: ✅ Working with real API

### ⚠️ Hotels API
- **Status**: No real API implemented (would need Booking.com, Expedia, etc.)
- **Current**: Uses mock data for all cities (but dynamically uses your city name)
- **Note**: This is a limitation - hotel booking APIs require partnerships

## Test Files vs Production

### Test Files (`tests/test_executor.py`)
- **Purpose**: Unit tests only
- **Hardcoded values**: Dallas/Austin are just test data
- **Impact**: **NONE** - These don't affect production code
- **Note**: Test files can have any hardcoded values for testing

### Production Code
- **Uses**: Your actual input (origin, destination from UI)
- **No hardcoding**: All values come from `user_request`
- **Dynamic**: Works for any city pair

## Changes Made

1. **Removed mock fallbacks on API errors**:
   - Places: Returns empty list instead of mock data
   - Maps: Returns error status instead of mock data
   - Weather: Returns error status instead of mock data

2. **Validation in planner**:
   - Checks LLM response matches user input
   - Auto-fixes any mismatches
   - Ensures all tools get correct city names

3. **Dynamic LLM fallback**:
   - Extracts origin/destination from prompt
   - Uses your actual input, not hardcoded values

## How to Verify

1. Check your `.env` file:
   ```bash
   USE_MOCKS=false
   GOOGLE_MAPS_API_KEY=your_key
   OPENWEATHER_API_KEY=your_key
   ```

2. Test with different cities:
   - Try: Dallas → San Antonio
   - Try: Houston → New York
   - Results should match your input

3. Check logs:
   - Look for "Google Maps API" calls
   - Look for "OpenWeather API" calls
   - Should NOT see "Falling back to mock data" (unless USE_MOCKS=true)

## Summary

✅ **Production code uses real APIs dynamically**
✅ **No hardcoded values in production code**
✅ **Test files are separate and don't affect production**
⚠️ **Hotels use mock data** (no real API available without partnerships)

The code is working as intended - using real APIs when available, and only falling back when APIs actually fail (not using mock data from files).

