#!/usr/bin/env python3
"""
Test script to verify your API keys are working.
"""
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def test_nemotron_key():
    """Test Nemotron API key."""
    api_base = os.getenv("LLM_API_BASE")
    api_key = os.getenv("LLM_API_KEY")
    
    if not api_base or not api_key:
        print("❌ Nemotron: No API key configured")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Simple test request
        payload = {
            "model": os.getenv("LLM_MODEL", "nvidia/nemotron-4-340b-reward"),
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Nemotron: API key working!")
            return True
        else:
            print(f"❌ Nemotron: API error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Nemotron: Connection failed - {e}")
        return False

def test_google_maps_key():
    """Test Google Maps API key."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key:
        print("⚠️  Google Maps: No API key configured (using mocks)")
        return True
        
    try:
        # Test geocoding API
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": "Austin, TX", "key": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200 and response.json().get("status") == "OK":
            print("✅ Google Maps: API key working!")
            return True
        else:
            print(f"❌ Google Maps: API error - {response.json().get('status', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Google Maps: Connection failed - {e}")
        return False

def test_openweather_key():
    """Test OpenWeather API key."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        print("⚠️  OpenWeather: No API key configured (using mocks)")
        return True
        
    try:
        # Test current weather API
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {"q": "Austin,TX", "appid": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ OpenWeather: API key working!")
            return True
        else:
            print(f"❌ OpenWeather: API error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenWeather: Connection failed - {e}")
        return False

def main():
    """Test all configured API keys."""
    print("🔑 Testing API Keys...")
    print("-" * 40)
    
    use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    if use_mocks:
        print("📋 Running in MOCK mode - no API keys needed")
        print("✅ All systems ready for demo!")
    else:
        print("🌐 Running in LIVE mode - testing API keys...")
        
        results = []
        results.append(test_nemotron_key())
        results.append(test_google_maps_key())
        results.append(test_openweather_key())
        
        print("-" * 40)
        
        if all(results):
            print("🎉 All API keys working! Ready for live mode!")
        elif results[0]:  # At least Nemotron works
            print("👍 Nemotron working! App will use AI + mock data for other services.")
        else:
            print("⚠️  Consider running in demo mode: set USE_MOCKS=true")
    
    print("\n🚀 Run the app with: streamlit run app.py")

if __name__ == "__main__":
    main()
