#!/usr/bin/env python3
"""
Test your NVIDIA Nemotron API key step by step.
"""
import requests
import json
import os
from dotenv import load_dotenv

def test_api_key_format(api_key):
    """Check if API key has correct format."""
    if not api_key:
        print("❌ No API key provided")
        return False
    
    if api_key.startswith('nvapi-'):
        print(f"✅ API key format looks correct: {api_key[:15]}...")
        return True
    elif api_key.startswith('your_') or 'placeholder' in api_key.lower():
        print(f"❌ API key is still placeholder: {api_key}")
        return False
    else:
        print(f"⚠️  Unusual API key format: {api_key[:15]}...")
        return True  # Might still work

def test_nvidia_api(api_key, model="nvidia/nemotron-nano-9b-v2"):
    """Test the NVIDIA API with your key."""
    
    api_base = "https://integrate.api.nvidia.com/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'Hello from Nemotron!' in exactly those words."}
        ],
        "max_tokens": 20,
        "temperature": 0.1
    }
    
    try:
        print(f"🚀 Testing API call to {model}...")
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            print("✅ SUCCESS! API is working!")
            print(f"🤖 Response: {content}")
            print(f"📈 Tokens used: {usage.get('total_tokens', 'Unknown')}")
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication Failed!")
            print("💡 Possible issues:")
            print("   - API key is incorrect")
            print("   - API key expired")
            print("   - API key not activated yet")
            return False
            
        elif response.status_code == 403:
            print("❌ Access Forbidden!")
            print("💡 Possible issues:")
            print("   - Model access not granted")
            print("   - Account needs verification")
            return False
            
        elif response.status_code == 404:
            print("❌ Model Not Found!")
            print(f"💡 Model '{model}' might not be available")
            print("   Try: nvidia/nemotron-4-340b-instruct")
            return False
            
        elif response.status_code == 429:
            print("⚠️  Rate Limited!")
            print("💡 Too many requests, wait and try again")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📄 Error: {error_detail}")
            except:
                print(f"📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out!")
        print("💡 API might be slow, try again")
        return False
        
    except requests.exceptions.ConnectionError:
        print("🌐 Connection failed!")
        print("💡 Check your internet connection")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main testing function."""
    print("🔑 NVIDIA Nemotron API Key Tester")
    print("=" * 50)
    
    # Load from .env file
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    
    if api_key:
        print("📂 Found API key in .env file")
        if test_api_key_format(api_key):
            if api_key.startswith('nvapi-'):
                test_nvidia_api(api_key)
            else:
                print("⚠️  Skipping API test due to key format")
        else:
            print("💡 Please update your .env file with a real API key")
    else:
        print("❌ No API key found in .env file")
        print()
        
        # Manual input option
        manual_key = input("🔑 Enter your API key to test (or press Enter to skip): ").strip()
        
        if manual_key:
            if test_api_key_format(manual_key):
                test_nvidia_api(manual_key)
                
                # Offer to save it
                save = input("\n💾 Save this key to .env file? (y/n): ").lower()
                if save == 'y':
                    try:
                        # Read current .env
                        env_path = ".env"
                        if os.path.exists(env_path):
                            with open(env_path, 'r') as f:
                                content = f.read()
                            
                            # Replace API key line
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if line.startswith('LLM_API_KEY='):
                                    lines[i] = f'LLM_API_KEY={manual_key}'
                                    break
                            
                            # Write back
                            with open(env_path, 'w') as f:
                                f.write('\n'.join(lines))
                            
                            print("✅ API key saved to .env file!")
                            
                        else:
                            print("❌ .env file not found")
                            
                    except Exception as e:
                        print(f"❌ Failed to save: {e}")
        else:
            print("⏭️  Skipping manual test")
    
    print("\n" + "=" * 50)
    print("🚀 Next Steps:")
    print("   1. If test passed: streamlit run app.py")
    print("   2. If test failed: check your API key")
    print("   3. Get API key from: https://build.nvidia.com/")

if __name__ == "__main__":
    main()
