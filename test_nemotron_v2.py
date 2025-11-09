#!/usr/bin/env python3
"""
Test script specifically for Nemotron V2 API access.
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nemotron_v2():
    """Test Nemotron V2 API key and model access."""
    
    api_base = os.getenv("LLM_API_BASE", "https://integrate.api.nvidia.com/v1")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "nvidia/nemotron-nano-9b-v2")
    
    print("🧪 Testing Nemotron V2 API Access...")
    print(f"📡 Endpoint: {api_base}")
    print(f"🤖 Model: {model}")
    print(f"🔑 API Key: {api_key[:20]}..." if api_key else "❌ No API key found")
    print("-" * 50)
    
    if not api_key:
        print("❌ No API key found!")
        print("💡 Add your key to .env file:")
        print("   LLM_API_KEY=nvapi-your-key-here")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test basic completion
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello! Can you help me plan a trip?"}
            ],
            "max_tokens": 50,
            "temperature": 0.3
        }
        
        print("🚀 Sending test request...")
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print("✅ SUCCESS! Nemotron V2 is working!")
            print(f"🤖 Model Response: {content[:100]}...")
            print(f"📈 Usage: {result.get('usage', 'Not provided')}")
            
            # Test structured output
            print("\n🧪 Testing structured JSON output...")
            structured_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that responds with valid JSON."},
                    {"role": "user", "content": 'Respond with JSON: {"status": "working", "message": "API test successful"}'}
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
            
            struct_response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=structured_payload,
                timeout=30
            )
            
            if struct_response.status_code == 200:
                struct_result = struct_response.json()
                struct_content = struct_result["choices"][0]["message"]["content"]
                print(f"📋 JSON Response: {struct_content}")
                
                # Try to parse as JSON
                try:
                    json.loads(struct_content.strip('```json').strip('```').strip())
                    print("✅ JSON parsing successful!")
                except:
                    print("⚠️  Response might need JSON cleaning (normal)")
                
                print("\n🎉 Nemotron V2 is fully ready for your itinerary agent!")
                return True
            else:
                print(f"⚠️  Structured test failed: {struct_response.status_code}")
                return True  # Basic test still passed
                
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("💡 Check your API key:")
            print("   1. Make sure it starts with 'nvapi-'")
            print("   2. Verify it's correctly set in .env file")
            print("   3. Try regenerating the key")
            return False
            
        elif response.status_code == 403:
            print("❌ Permission denied!")
            print("💡 Possible issues:")
            print("   1. Model access not granted")
            print("   2. Account needs verification")
            print("   3. Try a different model name")
            return False
            
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded!")
            print("💡 Wait a moment and try again")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out!")
        print("💡 The API might be slow, try again")
        return False
        
    except requests.exceptions.ConnectionError:
        print("🌐 Connection error!")
        print("💡 Check your internet connection")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_env_template():
    """Show the correct .env template for Nemotron V2."""
    print("\n📋 Your .env file should look like this:")
    print("-" * 40)
    print("""# Nemotron V2 Configuration
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-actual-key-here
LLM_MODEL=nvidia/nemotron-nano-9b-v2
LLM_PROVIDER=openai_compatible
USE_MOCKS=false

# Optional: Weather demo
WEATHER_DEMO_MODE=sunny
""")
    print("-" * 40)
    print("🔗 Get your API key from: https://build.nvidia.com/")

if __name__ == "__main__":
    success = test_nemotron_v2()
    
    if not success:
        show_env_template()
    else:
        print("\n🚀 Ready to run your agent with:")
        print("   streamlit run app.py")
