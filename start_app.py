#!/usr/bin/env python3
"""
Simple script to start both backend and frontend servers
"""
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    """Start the web application."""
    base_dir = Path(__file__).parent
    
    print("🧳 Nemotron Itinerary Agent - Web Application")
    print("=" * 60)
    print()
    
    # Check if Flask is installed
    try:
        import flask
        import flask_cors
    except ImportError:
        print("⚠️  Flask not found. Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed!")
        print()
    
    # Change to base directory
    os.chdir(base_dir)
    
    # Start backend (using port 5001 to avoid AirPlay Receiver conflict)
    os.environ['PORT'] = '5001'
    print("🚀 Starting backend server on http://localhost:5001...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "backend.app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for backend to start
    time.sleep(3)
    
    # Check if backend is running
    try:
        import requests
        response = requests.get("http://localhost:5001/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print("⚠️  Backend may not be fully ready yet")
    except ImportError:
        print("⚠️  'requests' not available for health check, but backend should be running")
    except:
        print("⚠️  Backend is starting... (this may take a moment)")
    
    print()
    
    # Start frontend
    print("🌐 Starting frontend server on http://localhost:8080...")
    frontend_dir = base_dir / 'frontend'
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(1)
    print("✅ Frontend is running!")
    print()
    
    # Print instructions
    print("=" * 60)
    print("✅ Application is running!")
    print()
    print("📱 Frontend: http://localhost:8080")
    print("🔧 Backend API: http://localhost:5001")
    print()
    print("Press Ctrl+C to stop both servers")
    print("=" * 60)
    print()
    
    # Try to open browser
    try:
        time.sleep(2)
        webbrowser.open("http://localhost:8080")
        print("🌐 Opening browser...")
    except:
        print("💡 Please open http://localhost:8080 in your browser")
    
    print()
    
    try:
        # Wait for user to stop
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n👋 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("✅ Servers stopped")

if __name__ == '__main__':
    main()

