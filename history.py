"""
City history generation tool using Google Gemini API.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_MOCKS = os.getenv("USE_MOCKS", "false").lower() == "true"


def generate_city_history(destination: str, max_length: int = 500) -> Dict[str, Any]:
    """
    Generate a brief history of the destination city using Gemini API.
    
    Args:
        destination: Name of the destination city
        max_length: Maximum length of the history text (default: 500 characters)
    
    Returns:
        Dict with status, history text, and metadata
    """
    if USE_MOCKS or not GEMINI_API_KEY:
        return _get_mock_history(destination)
    
    try:
        # Gemini API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        # Create prompt for city history
        prompt = f"""Write a brief, engaging history of {destination} in approximately {max_length} characters or less. 
        
Focus on:
- Key historical events or periods
- Important cultural or historical significance
- Notable facts that travelers would find interesting
- How the city developed into what it is today

Keep it concise, informative, and travel-friendly. Write in a friendly, accessible tone."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 500,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract text from Gemini response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        history_text = parts[0]["text"].strip()
                        
                        # Truncate if too long
                        if len(history_text) > max_length:
                            history_text = history_text[:max_length].rsplit('.', 1)[0] + '.'
                        
                        logger.info(f"Generated history for {destination} ({len(history_text)} characters)")
                        
                        return {
                            "status": "success",
                            "destination": destination,
                            "history": history_text,
                            "source": "gemini_api",
                            "length": len(history_text)
                        }
            
            # If response structure is unexpected, log and return fallback
            logger.warning(f"Unexpected Gemini API response structure: {data}")
            return _get_mock_history(destination)
        
        else:
            error_msg = response.text
            logger.error(f"Gemini API error: {response.status_code} - {error_msg}")
            return _get_mock_history(destination)
    
    except Exception as e:
        logger.error(f"Failed to generate city history with Gemini API: {e}")
        return _get_mock_history(destination)


def _get_mock_history(destination: str) -> Dict[str, Any]:
    """Generate mock city history for testing or when API is unavailable."""
    
    # Mock histories for common destinations
    mock_histories = {
        "austin": "Austin, Texas, was founded in 1839 and named after Stephen F. Austin, the 'Father of Texas'. Originally a small frontier settlement, it became the capital of the Republic of Texas in 1839 and later the state capital. Known for its music scene, Austin earned the nickname 'Live Music Capital of the World' and is home to major festivals like South by Southwest (SXSW) and Austin City Limits.",
        "new york": "New York City, originally called New Amsterdam when founded by Dutch settlers in 1624, became New York when the English took control in 1664. It grew into America's largest city and a global financial and cultural center. The city's iconic landmarks like the Statue of Liberty, Empire State Building, and Central Park reflect its rich history as a gateway for immigrants and a hub of innovation.",
        "los angeles": "Los Angeles was founded in 1781 by Spanish settlers and became part of Mexico before joining the United States in 1848. The discovery of oil in the 1890s and the arrival of the film industry in the early 20th century transformed LA into a global entertainment capital. Today, it's known for Hollywood, diverse neighborhoods, and its role as a cultural and economic powerhouse.",
        "san francisco": "San Francisco, originally a Spanish mission settlement in 1776, boomed during the California Gold Rush of 1849, growing from a small village to a major city. The 1906 earthquake and fire destroyed much of the city, but it was quickly rebuilt. Known for the Golden Gate Bridge, Alcatraz Island, and its progressive culture, San Francisco remains a center of innovation and diversity.",
        "chicago": "Chicago was incorporated as a city in 1837 and quickly grew into a major transportation hub thanks to its location on Lake Michigan and central position in America. The Great Chicago Fire of 1871 destroyed much of the city, but it was rebuilt with innovative architecture, including the world's first skyscrapers. Today, Chicago is known for its architecture, deep-dish pizza, blues music, and vibrant neighborhoods."
    }
    
    destination_lower = destination.lower()
    
    # Try to find a matching mock history
    for city_key, history in mock_histories.items():
        if city_key in destination_lower or destination_lower in city_key:
            return {
                "status": "success",
                "destination": destination,
                "history": history,
                "source": "mock",
                "length": len(history)
            }
    
    # Generic fallback history
    generic_history = f"{destination} is a vibrant city with a rich history and cultural heritage. The city has grown from its early beginnings to become an important destination known for its unique character, landmarks, and contributions to culture and commerce."
    
    return {
        "status": "success",
        "destination": destination,
        "history": generic_history,
        "source": "mock_generic",
        "length": len(generic_history)
    }

