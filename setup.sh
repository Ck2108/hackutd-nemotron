#!/bin/bash
# Setup script for Nemotron Itinerary Agent Web Application

echo "🧳 Nemotron Itinerary Agent - Web Application Setup"
echo "===================================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || {
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
}

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    echo "❌ Error: Please run this script from the Demo1 directory"
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt || {
    echo "❌ Failed to install dependencies. Please check your pip installation."
    exit 1
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To run the application:"
echo "   python3 start_app.py"
echo ""
echo "Or use:"
echo "   ./start_web.sh"
echo ""

