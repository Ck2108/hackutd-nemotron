# 🌐 Web Application - Nemotron Itinerary Agent

This is the web version of the Nemotron Itinerary Agent, built with HTML, Tailwind CSS, JavaScript, and Flask.

## 🚀 Quick Start

### Option 1: Run Both Backend and Frontend Together

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web application (starts both backend and frontend)
python run_web.py
```

This will start:
- **Backend API**: http://localhost:5000
- **Frontend**: http://localhost:8080

The application will automatically open in your browser.

### Option 2: Run Backend and Frontend Separately

#### Terminal 1: Backend
```bash
cd Demo1
python -m backend.app
# Or: python backend/app.py
```

#### Terminal 2: Frontend
```bash
cd Demo1/frontend
python -m http.server 8080
# Or use any static file server
```

Then open http://localhost:8080 in your browser.

## 📁 Project Structure

```
Demo1/
├── backend/
│   ├── __init__.py
│   └── app.py          # Flask API server
├── frontend/
│   ├── index.html      # Main HTML file
│   └── app.js          # JavaScript for interactions
├── agent/              # Agent logic (shared)
├── tools/              # Tools (shared)
├── run_web.py          # Script to run both servers
└── requirements.txt    # Python dependencies
```

## 🔧 Configuration

### API Base URL

The frontend is configured to use `http://localhost:5000/api` by default. To change this, edit `frontend/app.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

### Environment Variables

The backend uses the same environment variables as the Streamlit app:

- `LLM_API_BASE`: Nemotron API base URL
- `LLM_API_KEY`: Nemotron API key
- `USE_MOCKS`: Use mock data (true/false)
- `WEATHER_DEMO_MODE`: Weather demo mode (sunny/rainy)

## 🎨 Features

### Frontend (HTML + Tailwind CSS + JavaScript)

- ✅ Responsive design with Tailwind CSS
- ✅ Modern, clean UI
- ✅ Interactive tabs for different views
- ✅ Leaflet.js maps (replacing Folium)
- ✅ Real-time progress updates
- ✅ Download options (JSON, Calendar)
- ✅ Music recommendations with Spotify/YouTube links
- ✅ Clothing suggestions with color palettes
- ✅ Budget breakdown with charts
- ✅ Agent execution log

### Backend (Flask API)

- ✅ RESTful API endpoints
- ✅ CORS enabled for frontend
- ✅ JSON serialization of Pydantic models
- ✅ Error handling and logging
- ✅ Health check endpoint

## 📡 API Endpoints

### POST /api/plan-trip

Plan a trip based on user request.

**Request Body:**
```json
{
  "origin": "Dallas, TX",
  "destination": "Austin, TX",
  "start_date": "2024-01-15",
  "end_date": "2024-01-17",
  "travelers": 2,
  "budget_total": 800,
  "interests": ["BBQ", "live music"],
  "use_mocks": false,
  "weather_mode": "sunny"
}
```

**Response:**
```json
{
  "user_request": {...},
  "agent_state": {...},
  "itinerary": {...}
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Nemotron Itinerary Agent API is running"
}
```

## 🛠️ Development

### Adding New Features

1. **Backend**: Add new endpoints in `backend/app.py`
2. **Frontend**: Add UI components in `frontend/index.html` and logic in `frontend/app.js`

### Testing

```bash
# Test backend
curl http://localhost:5000/api/health

# Test trip planning
curl -X POST http://localhost:5000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Dallas, TX",
    "destination": "Austin, TX",
    "start_date": "2024-01-15",
    "end_date": "2024-01-17",
    "travelers": 2,
    "budget_total": 800,
    "interests": ["BBQ"]
  }'
```

## 🐛 Troubleshooting

### CORS Errors

If you see CORS errors, make sure:
1. Flask-CORS is installed: `pip install flask-cors`
2. CORS is enabled in `backend/app.py`: `CORS(app)`

### Import Errors

If you see import errors, make sure:
1. You're running from the correct directory
2. Python path includes the parent directory
3. All dependencies are installed

### Map Not Loading

If the map doesn't load:
1. Check browser console for errors
2. Make sure Leaflet.js is loaded (check network tab)
3. Check if map points are in the itinerary data

## 📝 Notes

- The web version uses Leaflet.js for maps instead of Folium (which is Streamlit-specific)
- All agent logic is shared between Streamlit and web versions
- The frontend is a single-page application (SPA)
- No build step required - just serve the HTML/JS files

## 🚀 Deployment

### Backend Deployment

You can deploy the Flask backend to:
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Run
- Any Python hosting service

### Frontend Deployment

The frontend is static files and can be deployed to:
- Netlify
- Vercel
- GitHub Pages
- Any static file hosting service

Remember to update the `API_BASE_URL` in `app.js` to point to your deployed backend.

