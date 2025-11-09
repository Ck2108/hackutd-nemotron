# 🔧 Quick Fix: Port 5000 Conflict

## Issue
Port 5000 was being used by macOS AirPlay Receiver, causing the backend to fail to start.

## Solution
Changed the backend port from 5000 to 5001.

## What Was Changed

1. **Backend Port**: Changed from 5000 → 5001
2. **Frontend API URL**: Updated to use port 5001
3. **Startup Scripts**: Updated to use port 5001

## How to Use

### If servers are already running:
1. **Refresh your browser page** (important - to load the updated JavaScript)
2. The frontend should now connect to the backend on port 5001

### If you need to restart:
```bash
cd Demo1
python3 start_app.py
```

Or manually:
```bash
# Terminal 1 - Backend
cd Demo1
PORT=5001 python3 -m backend.app

# Terminal 2 - Frontend  
cd Demo1/frontend
python3 -m http.server 8080
```

## Verify It's Working

1. Backend health check:
   ```bash
   curl http://localhost:5001/api/health
   ```
   Should return: `{"status":"healthy","message":"Nemotron Itinerary Agent API is running"}`

2. Open http://localhost:8080 in your browser
3. **Refresh the page** to load the updated JavaScript
4. Try planning a trip - it should work now!

## Current Status

✅ Backend: Running on http://localhost:5001
✅ Frontend: Running on http://localhost:8080
✅ API URL: Updated to http://localhost:5001/api

## Note

If you still see "Failed to fetch":
1. Make sure you **refreshed the browser page** (Ctrl+R or Cmd+R)
2. Check browser console (F12) for any errors
3. Verify backend is running: `curl http://localhost:5001/api/health`

