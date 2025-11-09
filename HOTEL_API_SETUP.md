# Hotel API Setup Guide

## ✅ What's Implemented

The hotel search now uses **Google Places API** to find real hotels in any city you specify. Here's what works:

### Current Implementation
- ✅ Searches for hotels using Google Places API
- ✅ Filters hotels by your budget (`max_price` parameter)
- ✅ Returns real hotel names, addresses, ratings, and locations
- ✅ Uses actual coordinates for the city you specify
- ✅ Falls back to mock data if API fails or is unavailable

### How It Works
1. When you search for hotels, it queries Google Places API with: `"hotels in [your city]"`
2. Filters results by `type: "lodging"` to get only hotels
3. Estimates price per night from Google's `price_level` (1-4 scale):
   - Level 1: ~$80/night (Inexpensive)
   - Level 2: ~$120/night (Moderate)
   - Level 3: ~$180/night (Expensive)
   - Level 4: ~$250/night (Very Expensive/Luxury)
4. Filters hotels that fit within your budget
5. Returns hotels sorted by price (cheapest first)

## 🔑 What You Need

### Required: Google Maps API Key
You already have this! Just make sure:
1. Your `.env` file has: `GOOGLE_MAPS_API_KEY=your_key_here`
2. The API key has **Places API** enabled (not just Directions API)
3. Enable it in Google Cloud Console: https://console.cloud.google.com/apis/library/places-backend.googleapis.com

### API Setup Steps
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Library**
4. Search for **"Places API"** (the new one, NOT "Places API (Legacy)")
5. Click **Enable**
6. **Important**: Make sure you disable "Places API (Legacy)" if it's enabled
7. Your existing API key should now work for hotels

**Note**: If you see the error "You're calling a legacy API", you need to:
- Disable "Places API (Legacy)" 
- Enable "Places API" (the new one)
- The new API uses the same endpoint but requires the new API to be enabled

## 📊 Current Limitations

### Price Estimation
- Google Places API doesn't provide actual booking prices
- We estimate prices from `price_level` (1-4 scale)
- Actual prices may vary based on dates, availability, and booking site

### Real-Time Pricing
For **real-time hotel prices**, you would need a hotel booking API:

#### Option 1: Amadeus Hotel API (Free Tier Available)
- **Cost**: Free tier: 2,000 requests/month
- **Setup**: 
  1. Sign up at https://developers.amadeus.com/
  2. Get API key and secret
  3. Add to `.env`: `AMADEUS_API_KEY=...` and `AMADEUS_API_SECRET=...`
- **Pros**: Free tier, real prices, availability
- **Cons**: Limited requests/month

#### Option 2: Booking.com API
- **Cost**: Requires partnership/affiliate program
- **Setup**: Contact Booking.com for API access
- **Pros**: Real prices, direct booking links
- **Cons**: Requires business partnership

#### Option 3: Expedia API
- **Cost**: Requires partnership
- **Setup**: Contact Expedia for API access
- **Pros**: Real prices, availability
- **Cons**: Requires business partnership

## 🚀 How to Use

### Current Setup (Google Places API)
1. Make sure `USE_MOCKS=false` in your `.env` (or don't set it, defaults to false)
2. Ensure `GOOGLE_MAPS_API_KEY` is set
3. Enable Places API in Google Cloud Console
4. Search for hotels - it will use real hotel data!

### Example
```python
from tools.hotels import search
from datetime import date

# Search for hotels in Houston, budget $150/night
hotels = search(
    city="Houston, TX",
    start_date=date(2024, 12, 1),
    end_date=date(2024, 12, 5),
    max_price=150.0,
    limit=10
)

# Returns real hotels from Google Places API!
```

## 🎯 What Works Now

✅ **Real Hotel Names**: Actual hotel names from Google Places  
✅ **Real Locations**: Correct coordinates for your city  
✅ **Real Ratings**: Google user ratings  
✅ **Budget Filtering**: Only shows hotels within your budget  
✅ **City-Specific**: Works for any city worldwide  
✅ **Addresses**: Real street addresses  

## ⚠️ What's Estimated

⚠️ **Prices**: Estimated from price_level, not actual booking prices  
⚠️ **Availability**: Not checked (assumes available)  
⚠️ **Real-Time Pricing**: Not available (would need booking API)  

## 💡 Future Enhancements

If you want real-time pricing, consider:
1. Integrating Amadeus Hotel API (free tier)
2. Using web scraping (not recommended, may violate ToS)
3. Partnering with booking sites for API access

For now, the Google Places API integration gives you real hotels in the right city, filtered by your budget!

