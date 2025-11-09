#!/usr/bin/env python3
"""
Quick verification script to check if .env file is fixed correctly.
"""
import os
from dotenv import load_dotenv

def verify_fixes():
    """Verify that the .env file has been fixed correctly."""
    print("🔍 VERIFYING YOUR .env FILE FIXES")
    print("=" * 50)
    
    # Reload environment variables
    load_dotenv(override=True)
    
    use_mocks = os.getenv("USE_MOCKS")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")
    
    print("📋 Current values:")
    print(f"   USE_MOCKS: {use_mocks}")
    print(f"   LLM_MODEL: {model}")
    print(f"   LLM_API_KEY: {api_key[:15]}..." if api_key else "   LLM_API_KEY: Not set")
    print()
    
    # Check fixes
    fixes_correct = 0
    total_fixes = 2
    
    # Check USE_MOCKS
    if use_mocks == "false":
        print("✅ Fix 1: USE_MOCKS=false (CORRECT)")
        fixes_correct += 1
    elif use_mocks == "true":
        print("❌ Fix 1: USE_MOCKS is still 'true' (NEEDS FIX)")
        print("   Should be: USE_MOCKS=false")
    else:
        print(f"❓ Fix 1: USE_MOCKS={use_mocks} (UNEXPECTED VALUE)")
    
    # Check model name
    if model == "nvidia/NVIDIA-Nemotron-Nano-9B-v2":
        print("✅ Fix 2: LLM_MODEL format correct (CORRECT)")
        fixes_correct += 1
    elif "nvidia/nvidia-" in model:
        print("❌ Fix 2: Model still has double 'nvidia/' prefix (NEEDS FIX)")
        print("   Current:", model)
        print("   Should be: nvidia/NVIDIA-Nemotron-Nano-9B-v2")
    else:
        print(f"❓ Fix 2: LLM_MODEL={model} (CHECK FORMAT)")
    
    print()
    print(f"🎯 FIXES COMPLETED: {fixes_correct}/{total_fixes}")
    
    if fixes_correct == total_fixes:
        print("🎉 ALL FIXES APPLIED CORRECTLY!")
        print()
        print("🚀 Now test your live API mode:")
        print("   1. python test_live_mode.py")
        print("   2. streamlit run app.py")
        print("   3. Look for 'Powered by Nemotron AI' message")
        
        # Quick API test
        print()
        print("🧪 Testing API connection...")
        try:
            from agent.llm import llm_client
            
            if not llm_client.use_mocks and llm_client.has_api_config:
                print("✅ LLM client configured for live mode")
                
                # Try a quick test
                response = llm_client.get_completion("Hello", max_tokens=10)
                if len(response) > 5 and "fallback" not in response.lower():
                    print("✅ API connection working!")
                    print(f"   Sample response: {response[:50]}...")
                else:
                    print("⚠️  API returning fallback - check connection")
            else:
                print("❌ LLM client still in mock mode")
                
        except Exception as e:
            print(f"⚠️  Error testing API: {e}")
            
    else:
        print("❌ FIXES STILL NEEDED!")
        print()
        print("📝 What to do:")
        print("1. Open your .env file in a text editor")
        print("2. Make the changes shown above")
        print("3. SAVE the file")
        print("4. Run this script again: python verify_fix.py")

if __name__ == "__main__":
    verify_fixes()
