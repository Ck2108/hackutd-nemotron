#!/bin/bash
# Start script for web application

echo "🧳 Nemotron Itinerary Agent - Web Application"
echo "=============================================="
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    echo "❌ Error: Please run this script from the Demo1 directory"
    exit 1
fi

echo "🚀 Starting backend server..."
echo ""

# Run backend in background
python3 -m backend.app &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo "🌐 Starting frontend server..."
echo ""

# Run frontend
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Application is running!"
echo "📱 Frontend: http://localhost:8080"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait

