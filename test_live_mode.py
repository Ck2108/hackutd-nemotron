#!/usr/bin/env python3
"""
Test script for live API mode (USE_MOCKS=false).
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_live_mode():
    """Test live API mode configuration."""
    print("🧪 TESTING LIVE API MODE (USE_MOCKS=false)")
    print("=" * 60)
    
    # Show current config
    use_mocks = os.getenv("USE_MOCKS", "true").lower()
    model = os.getenv("LLM_MODEL", "not set")
    api_key = os.getenv("LLM_API_KEY", "not set")
    
    print("📋 Configuration Check:")
    print(f"   USE_MOCKS: {use_mocks}")
    print(f"   LLM_MODEL: {model}")
    print(f"   API_KEY: {api_key[:15]}..." if len(api_key) > 15 else f"   API_KEY: {api_key}")
    print()
    
    # Check for issues
    issues = []
    
    if use_mocks == "true":
        issues.append("❌ USE_MOCKS is still 'true' - should be 'false' for live mode")
    
    if "nvidia/nvidia-" in model:
        issues.append("❌ Model name has double 'nvidia/' prefix")
        issues.append(f"   Current: {model}")
        issues.append(f"   Should be: nvidia/NVIDIA-Nemotron-Nano-9B-v2")
    
    if not api_key.startswith("nvapi-"):
        issues.append("❌ API key doesn't start with 'nvapi-'")
    
    # Show results
    if issues:
        print("🔧 ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print()
        print("💡 FIX YOUR .env FILE:")
        print("   USE_MOCKS=false")
        print("   LLM_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2")
        print("   LLM_API_KEY=nvapi-your-real-key")
    else:
        print("✅ CONFIGURATION LOOKS CORRECT!")
        print()
        
        # Test the agent components
        try:
            print("🧠 Testing agent components...")
            from agent.llm import llm_client
            
            print(f"   LLM client configured: {llm_client.has_api_config}")
            print(f"   Using mocks: {llm_client.use_mocks}")
            print(f"   Model: {llm_client.model}")
            
            if not llm_client.use_mocks and llm_client.has_api_config:
                print("🚀 Attempting live API test...")
                
                # Simple test
                response = llm_client.get_completion("Hello! Can you help plan a trip?", max_tokens=30)
                
                if len(response) > 20 and "fallback" not in response.lower():
                    print("✅ LIVE API MODE WORKING!")
                    print(f"   Response: {response[:80]}...")
                else:
                    print("⚠️  API call returned fallback response")
                    print(f"   Response: {response[:80]}...")
            else:
                print("⚠️  Still using fallback mode")
                
        except Exception as e:
            print(f"❌ Error testing components: {e}")
    
    print()
    print("🚀 Next steps:")
    if issues:
        print("   1. Fix the issues above in your .env file")
        print("   2. Run this test again: python test_live_mode.py")
        print("   3. Run your app: streamlit run app.py")
    else:
        print("   1. Run your app: streamlit run app.py")
        print("   2. Should see 'Powered by Nemotron AI' message")
        print("   3. Agent will use real AI planning!")

if __name__ == "__main__":
    test_live_mode()
