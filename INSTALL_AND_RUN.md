# 🚀 Installation and Run Guide

## Quick Start (Easiest Way)

### Option 1: Using the Python Script (Recommended)

```bash
cd Demo1
python3 start_app.py
```

This will:
1. Check and install dependencies if needed
2. Start the backend server (port 5000)
3. Start the frontend server (port 8080)
4. Open your browser automatically

### Option 2: Using the Shell Script

```bash
cd Demo1
./start_web.sh
```

### Option 3: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd Demo1
python3 -m backend.app
```

**Terminal 2 - Frontend:**
```bash
cd Demo1/frontend
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

## Installation

### Step 1: Install Python Dependencies

```bash
cd Demo1
pip install -r requirements.txt
```

Or if you need to use pip3:
```bash
pip3 install -r requirements.txt
```

### Step 2: Verify Installation

Check if Flask is installed:
```bash
python3 -c "import flask; print('Flask installed:', flask.__version__)"
```

### Step 3: Run the Application

Use one of the methods above.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"

**Solution:**
Kill the process using port 5000:
```bash
# On macOS/Linux:
lsof -ti:5000 | xargs kill -9

# Or change the port in backend/app.py
```

### Issue: "Port 8080 already in use"

**Solution:**
Kill the process using port 8080:
```bash
# On macOS/Linux:
lsof -ti:8080 | xargs kill -9

# Or use a different port in start_app.py
```

### Issue: "CORS errors in browser"

**Solution:**
Make sure Flask-CORS is installed:
```bash
pip install flask-cors
```

### Issue: "Import errors"

**Solution:**
Make sure you're running from the `Demo1` directory:
```bash
cd Demo1
python3 -m backend.app
```

### Issue: "Backend not responding"

**Solution:**
1. Check if backend is running: `curl http://localhost:5000/api/health`
2. Check backend logs for errors
3. Make sure all environment variables are set correctly

## Environment Variables

Create a `.env` file in the `Demo1` directory (optional):

```env
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL=nvidia/nemotron-4-340b-reward
USE_MOCKS=true
WEATHER_DEMO_MODE=sunny
```

Or set them in your shell:
```bash
export USE_MOCKS=true
export WEATHER_DEMO_MODE=sunny
```

## Testing

### Test Backend Health

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status":"healthy","message":"Nemotron Itinerary Agent API is running"}
```

### Test Trip Planning

```bash
curl -X POST http://localhost:5000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Dallas, TX",
    "destination": "Austin, TX",
    "start_date": "2024-01-15",
    "end_date": "2024-01-17",
    "travelers": 2,
    "budget_total": 800,
    "interests": ["BBQ", "live music"],
    "use_mocks": true
  }'
```

## File Structure

```
Demo1/
├── backend/
│   ├── __init__.py
│   └── app.py              # Flask API server
├── frontend/
│   ├── index.html          # Main HTML file
│   └── app.js              # JavaScript logic
├── agent/                  # Agent logic
├── tools/                  # Tools (maps, weather, etc.)
├── start_app.py            # Main startup script (RECOMMENDED)
├── start_web.sh            # Shell startup script
├── run_web.py              # Alternative Python startup script
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (optional)
```

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Run the app: `python3 start_app.py`
3. ✅ Open http://localhost:8080 in your browser
4. ✅ Plan a trip and test all features!

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Check the browser console for errors (F12)
3. Check the backend logs for errors
4. Make sure all dependencies are installed
5. Verify you're running from the correct directory

