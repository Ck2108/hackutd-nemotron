# 🌐 Web Application - Quick Start Guide

## ✅ What Was Created

The Streamlit application has been converted to a modern web application with:

- **Backend**: Flask REST API (`backend/app.py`)
- **Frontend**: HTML + Tailwind CSS + JavaScript (`frontend/`)
- **Maps**: Leaflet.js (replacing Folium)
- **Styling**: Tailwind CSS (via CDN)

## 🚀 How to Run

### Step 1: Install Dependencies

```bash
cd Demo1
pip install -r requirements.txt
```

This will install Flask, Flask-CORS, and all other dependencies.

### Step 2: Run the Application

#### Option A: Using the Start Script (Recommended)

```bash
./start_web.sh
```

#### Option B: Manual Start

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

### Step 3: Open in Browser

Open http://localhost:8080 in your browser.

The backend API will be running on http://localhost:5000.

## 📁 File Structure

```
Demo1/
├── backend/
│   ├── __init__.py
│   └── app.py              # Flask API server
├── frontend/
│   ├── index.html          # Main HTML file
│   └── app.js              # JavaScript logic
├── start_web.sh            # Start script
├── run_web.py              # Python start script
└── README_WEB.md           # Detailed documentation
```

## 🎨 Features

### Frontend Features

- ✅ Responsive design with Tailwind CSS
- ✅ Interactive tabs (Schedule, Budget, Map, Clothing, Music)
- ✅ Leaflet.js maps with custom markers
- ✅ Real-time progress updates
- ✅ Download options (JSON)
- ✅ Music recommendations with Spotify/YouTube links
- ✅ Clothing suggestions with color palettes
- ✅ Budget breakdown with visualizations

### Backend Features

- ✅ RESTful API endpoints
- ✅ CORS enabled
- ✅ JSON serialization
- ✅ Error handling
- ✅ Health check endpoint

## 🔧 Configuration

### Change API URL

Edit `frontend/app.js`:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

### Environment Variables

Same as Streamlit app:
- `LLM_API_BASE`: Nemotron API URL
- `LLM_API_KEY`: Nemotron API key
- `USE_MOCKS`: Use mock data
- `WEATHER_DEMO_MODE`: Weather mode (sunny/rainy)

## 🐛 Troubleshooting

### CORS Errors

Make sure Flask-CORS is installed:
```bash
pip install flask-cors
```

### Import Errors

Make sure you're running from the `Demo1` directory:
```bash
cd Demo1
python3 -m backend.app
```

### Map Not Loading

1. Check browser console for errors
2. Make sure Leaflet.js is loaded (check network tab)
3. Verify map points exist in itinerary data

### Port Already in Use

Change ports in:
- Backend: `backend/app.py` (default: 5000)
- Frontend: `start_web.sh` or `run_web.py` (default: 8080)

## 📝 Notes

- The web app uses the same agent logic as the Streamlit version
- All features (clothing, music, maps) work the same way
- The frontend is a single-page application (SPA)
- No build step required - just serve the HTML/JS files

## 🚀 Next Steps

1. Test the application with a sample trip
2. Customize the styling in `frontend/index.html`
3. Add new features in `frontend/app.js`
4. Deploy to a hosting service (see README_WEB.md)

## 📚 More Information

See `README_WEB.md` for detailed documentation on:
- API endpoints
- Deployment options
- Development guide
- Advanced configuration

