#!/usr/bin/env python3
"""
Run the web application (Flask backend + serve frontend)
"""
import os
import sys
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def run_backend():
    """Run Flask backend server."""
    # Change to the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Add to path
    sys.path.insert(0, str(script_dir))
    
    from backend.app import app
    port = int(os.environ.get('PORT', 5001))  # Changed to 5001 to avoid AirPlay Receiver conflict
    print(f"🚀 Starting Flask backend on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)

def run_frontend():
    """Run frontend HTTP server."""
    script_dir = Path(__file__).parent.absolute()
    frontend_dir = script_dir / 'frontend'
    
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(frontend_dir), **kwargs)
        
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    port = 8080
    server = HTTPServer(('localhost', port), Handler)
    print(f"🌐 Starting frontend server on http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    print("🧳 Nemotron Itinerary Agent - Web Application")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(2)
    
    # Start frontend in a separate thread
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    frontend_thread.start()
    
    # Wait a bit for frontend to start
    time.sleep(1)
    
    # Open browser
    print("\n✅ Application is running!")
    print("📱 Frontend: http://localhost:8080")
    print("🔧 Backend API: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

