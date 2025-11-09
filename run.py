#!/usr/bin/env python3
"""
Quick start script for the Nemotron Itinerary Agent.
"""
import subprocess
import sys
import os

def main():
    """Run the Streamlit app with proper configuration."""
    
    print("🧳 Starting Nemotron Itinerary Agent...")
    print("📍 Open your browser to http://localhost:8501 when ready")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Set default environment (use .env file for configuration)
    # Default to live API mode unless USE_MOCKS is explicitly set
    if "USE_MOCKS" not in os.environ:
        os.environ["USE_MOCKS"] = "false"
    os.environ.setdefault("WEATHER_DEMO_MODE", "sunny")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Thanks for using Nemotron Itinerary Agent!")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        print("\n💡 Try running directly with: streamlit run app.py")

if __name__ == "__main__":
    main()
