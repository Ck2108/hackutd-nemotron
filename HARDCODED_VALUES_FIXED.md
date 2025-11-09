# Hardcoded Values Fixed

## Issues Found

You were correct! There were hardcoded Dallas→Austin values in multiple places that were overriding user input:

### 1. ❌ LLM Fallback JSON (agent/llm.py)
**Problem**: The `_get_fallback_json` method had hardcoded:
- Origin: "Dallas, TX"
- Destination: "Austin, TX"
- Interests: "BBQ", "live music"

**Impact**: When the LLM API failed or returned invalid JSON, it would use these hardcoded values instead of the user's input.

### 2. ❌ LLM Fallback Text (agent/llm.py)
**Problem**: The `_get_fallback_completion` method had hardcoded Dallas→Austin text.

### 3. ⚠️ No Validation in Planner
**Problem**: The planner didn't validate that LLM responses matched the user's request. Even if the LLM returned valid JSON with wrong cities, it would be accepted.

## Fixes Applied

### ✅ 1. Dynamic LLM Fallback
- Updated `_get_fallback_json` to extract origin, destination, interests, and budget from the prompt using regex
- Now uses the actual user's input instead of hardcoded values
- Falls back to generic values only if extraction fails

### ✅ 2. Planner Validation
- Added validation in `create_plan` to check if LLM response matches `user_request`
- Automatically fixes any mismatches (origin, destination, dates, city)
- Logs warnings when mismatches are detected and fixed
- Ensures all tool params use the correct user input

### ✅ 3. Mock Data Tools
- Mock data tools already work for any city (they use Austin data as a template)
- City names in results come from user input, not hardcoded

## How It Works Now

1. **User enters**: Dallas → San Antonio
2. **LLM receives**: Prompt with "Origin: Dallas, TX", "Destination: San Antonio, TX"
3. **If LLM fails**: Fallback extracts "San Antonio, TX" from prompt
4. **If LLM returns wrong city**: Planner validates and fixes to "San Antonio, TX"
5. **Tools receive**: Correct city from user_request
6. **Results show**: San Antonio hotels, places, weather

## Testing

Try planning a trip from:
- Dallas → San Antonio
- Houston → New York
- Any origin → Any destination

The agent should now use your actual input, not hardcoded Dallas→Austin values.

## Files Changed

1. `agent/llm.py` - Dynamic fallback extraction
2. `agent/planner.py` - Validation and auto-fix of mismatches
3. `tools/places.py` - Updated comments (already worked for any city)
4. `tools/hotels.py` - Updated comments (already worked for any city)

