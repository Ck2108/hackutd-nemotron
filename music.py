"""
Music recommendation tool with LLM-powered location-based song suggestions for social media.
"""
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from agent.llm import llm_client

logger = logging.getLogger(__name__)


def get_location_music_genres(destination: str) -> List[str]:
    """
    Get typical music genres associated with a location.
    
    Returns: List of genres popular in that location
    """
    destination_lower = destination.lower()
    
    # Location-based genre mapping
    genre_map = {
        # West Coast
        "los angeles": ["Pop", "Hip-Hop", "R&B", "Rock", "Latin"],
        "san francisco": ["Indie Rock", "Electronic", "Alternative", "Folk"],
        "san diego": ["Surf Rock", "Pop", "Reggae", "Latin"],
        "california": ["Pop", "Hip-Hop", "Rock", "Latin", "Electronic"],
        
        # East Coast
        "new york": ["Hip-Hop", "Pop", "Jazz", "Rock", "Electronic"],
        "boston": ["Rock", "Folk", "Indie", "Alternative"],
        "philadelphia": ["Hip-Hop", "Soul", "Rock", "R&B"],
        
        # Southern
        "austin": ["Country", "Rock", "Blues", "Indie", "Folk"],
        "houston": ["Hip-Hop", "Country", "R&B", "Latin"],
        "dallas": ["Country", "Hip-Hop", "Rock", "Pop"],
        "atlanta": ["Hip-Hop", "R&B", "Trap", "Pop"],
        "nashville": ["Country", "Folk", "Rock", "Bluegrass"],
        "miami": ["Latin", "Reggaeton", "Hip-Hop", "Electronic", "Pop"],
        "texas": ["Country", "Rock", "Blues", "Hip-Hop"],
        "florida": ["Latin", "Pop", "Hip-Hop", "Electronic"],
        
        # Northern
        "chicago": ["Blues", "Jazz", "Hip-Hop", "Rock", "House"],
        "detroit": ["Motown", "Hip-Hop", "Techno", "Soul"],
        "minneapolis": ["Pop", "Rock", "Indie", "Hip-Hop"],
        
        # Mountain/West
        "denver": ["Rock", "Folk", "Country", "Indie"],
        "seattle": ["Grunge", "Indie Rock", "Alternative", "Folk"],
        "portland": ["Indie", "Folk", "Alternative", "Rock"],
        
        # Desert
        "phoenix": ["Country", "Rock", "Latin", "Hip-Hop"],
        "las vegas": ["Electronic", "Pop", "Hip-Hop", "Rock"],
    }
    
    # Check for exact matches first
    for location, genres in genre_map.items():
        if location in destination_lower:
            return genres
    
    # Default genres based on region keywords
    if any(keyword in destination_lower for keyword in ["california", "oregon", "washington"]):
        return ["Pop", "Rock", "Indie", "Electronic"]
    elif any(keyword in destination_lower for keyword in ["texas", "austin", "houston", "dallas"]):
        return ["Country", "Rock", "Hip-Hop", "Blues"]
    elif any(keyword in destination_lower for keyword in ["florida", "miami", "orlando"]):
        return ["Latin", "Pop", "Hip-Hop", "Electronic"]
    elif any(keyword in destination_lower for keyword in ["new york", "ny", "manhattan"]):
        return ["Hip-Hop", "Pop", "Jazz", "Rock"]
    else:
        # Default popular genres
        return ["Pop", "Rock", "Hip-Hop", "Electronic"]


def recommend_music(
    destination: str,
    season: Optional[str] = None,
    climate_zone: Optional[str] = None,
    mood: str = "vibrant"
) -> Dict[str, Any]:
    """
    Generate music recommendations based on location using LLM.
    
    Args:
        destination: Destination city/state name
        season: Season (spring, summer, fall, winter)
        climate_zone: Climate zone (west_coast, southern, etc.)
        mood: Mood for the music (vibrant, chill, energetic, relaxed, etc.)
    
    Returns:
        Dictionary with music recommendations including songs, artists, genres
    """
    try:
        # Get location-based genres
        location_genres = get_location_music_genres(destination)
        genres_str = ", ".join(location_genres)
        
        # Build enhanced prompt for music recommendations
        season_context = f" during {season.title()} season" if season else ""
        climate_context = f" The location has a {climate_zone.replace('_', ' ')} climate" if climate_zone else ""
        
        prompt = f"""You are a music curator and social media expert. Recommend popular and trending songs perfect for social media posts (Instagram stories, TikTok, Reels) for a trip to {destination}{season_context}.{climate_context}

LOCATION CONTEXT:
- Destination: {destination}
- Popular Genres in Area: {genres_str}
- Season: {season.title() if season else 'Any'}
- Mood: {mood}

REQUIREMENTS:
1. **LOCATION-RELEVANT**: Include songs that are popular or associated with this location/region
2. **SOCIAL MEDIA READY**: Songs that work well for travel content, vacation vibes, and location showcases
3. **GENRE VARIETY**: Include a mix of {genres_str} and other popular genres
4. **TRENDING & TIMELESS**: Mix of current hits and classic tracks that resonate with the location
5. **MOOD APPROPRIATE**: Songs that match {mood} vibes for travel content

FOR EACH SONG, PROVIDE:
- **Song Title**: Exact song name
- **Artist**: Artist/band name
- **Genre**: Music genre (e.g., Pop, Hip-Hop, Country, Rock, Latin, Electronic)
- **Mood/Energy**: Energy level and mood (e.g., "Upbeat", "Chill", "Energetic", "Relaxed")
- **Why This Song**: Brief reason why it fits this location (1 sentence)
- **Best For**: Type of social media content (e.g., "Instagram Stories", "TikTok", "Reels", "Photo Slideshows")

Provide 8-12 diverse song recommendations that capture the vibe of {destination}. Include a mix of:
- Location-specific anthems
- Popular travel/vacation songs
- Trending hits
- Classic tracks associated with the area

Format your response with clear song recommendations and details."""

        # Get LLM completion
        response = llm_client.get_completion(prompt, max_tokens=2000)
        
        # Parse response and create structured output
        recommendations = _parse_music_response(response, destination, location_genres)
        
        return {
            "status": "success",
            "destination": destination,
            "location_genres": location_genres,
            "season": season,
            "mood": mood,
            "recommendations": recommendations,
            "raw_llm_response": response
        }
        
    except Exception as e:
        logger.error(f"Failed to generate music recommendations: {e}")
        return _get_fallback_music_recommendations(destination, location_genres, season)


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting from text."""
    if not text:
        return ""
    
    # Remove markdown bold/italic (**, *, __, _)
    text = text.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
    
    # Remove leading/trailing dots, dashes, and other markdown artifacts
    text = text.strip('. -–—•')
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()


def _clean_song_name(name: str) -> str:
    """Clean and format song name for better readability."""
    if not name:
        return ""
    
    # Remove markdown formatting first
    name = _strip_markdown(name)
    
    # Remove extra whitespace but preserve structure
    name = " ".join(name.split())
    
    # Remove outer quotes and brackets, but preserve commas and apostrophes
    name = name.strip('"\'()[]{}')
    
    # Split into words, preserving separators
    # Split by spaces but keep track of punctuation
    words = name.split()
    if not words:
        return name
    
    # Title case each word, but handle special cases
    cleaned_words = []
    for i, word in enumerate(words):
        # Preserve punctuation at the end (like commas, apostrophes)
        punctuation_end = ""
        punctuation_start = ""
        
        # Extract trailing punctuation (but keep commas and apostrophes in the word)
        if word and word[-1] in ',;:!?':
            punctuation_end = word[-1]
            word = word[:-1]
        
        # Extract leading punctuation
        if word and word[0] in '"\'(':
            punctuation_start = word[0]
            word = word[1:]
        
        if not word:
            cleaned_words.append(punctuation_start + punctuation_end)
            continue
        
        # Preserve common prepositions and articles in lowercase (except first word)
        lowercase_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        if word.lower() in lowercase_words and i > 0:
            cleaned_word = word.lower()
        else:
            # Title case, but handle special cases
            # Handle words with apostrophes (e.g., "Dreamin'" -> "Dreamin'")
            if "'" in word:
                parts = word.split("'")
                cleaned_word = "'".join([p.capitalize() if p else "" for p in parts])
            else:
                cleaned_word = word.capitalize()
        
        cleaned_words.append(punctuation_start + cleaned_word + punctuation_end)
    
    result = " ".join(cleaned_words)
    # Clean up any double spaces that might have been created
    result = " ".join(result.split())
    
    return result


def _clean_artist_name(artist: str) -> str:
    """Clean and format artist name for better readability."""
    if not artist:
        return ""
    
    # Remove markdown formatting first
    artist = _strip_markdown(artist)
    
    # Remove extra whitespace
    artist = " ".join(artist.split())
    
    # Remove outer quotes and brackets
    artist = artist.strip('"\'()[]{}')
    
    # Handle featured artists and collaborations
    parts = artist.split()
    cleaned_parts = []
    
    for i, part in enumerate(parts):
        # Preserve period for abbreviations, but strip other punctuation initially
        # Check if it's an abbreviation before stripping
        has_trailing_period = part.endswith('.') and len(part) <= 4  # Likely abbreviation
        part_clean = part.strip('.,;:!?') if not has_trailing_period else part.rstrip(';:!?')
        
        if not part_clean:
            continue
        
        # Handle featured/collaboration markers
        if part_clean.lower() in ['ft', 'ft.', 'feat', 'feat.', 'featuring', 'featuring.']:
            # Standardize to "ft."
            cleaned_parts.append('ft.')
        elif part_clean.lower() == '&' or part_clean == '&':
            cleaned_parts.append('&')
        elif part_clean.lower() == 'and' and i > 0:  # "and" between artists
            cleaned_parts.append('&')
        elif part_clean.lower() == 'vs' or part_clean.lower() == 'vs.':
            cleaned_parts.append('vs.')
        elif part_clean.lower() == 'x' or part_clean == 'x':  # Collaboration marker
            cleaned_parts.append('×')
        else:
            # Title case artist names, handling special characters
            # Handle hyphens (e.g., "Jay-Z" -> "Jay-Z")
            if '-' in part_clean:
                hyphen_parts = part_clean.split('-')
                cleaned_part = '-'.join([p.capitalize() if p else '' for p in hyphen_parts])
            # Handle apostrophes (e.g., "O'Brien" -> "O'Brien")
            elif "'" in part_clean:
                apostrophe_parts = part_clean.split("'")
                cleaned_part = "'".join([p.capitalize() if p else "" for p in apostrophe_parts])
            # Handle names starting with numbers (e.g., "2pac" -> "2Pac")
            elif part_clean[0].isdigit():
                # Capitalize the first letter after the number(s)
                cleaned_part = part_clean[0]
                if len(part_clean) > 1:
                    cleaned_part += part_clean[1:].capitalize()
            # Handle common abbreviations (Dr, Mr, Ms, etc.)
            elif part_clean.lower() in ['dr', 'mr', 'ms', 'mrs', 'jr', 'sr']:
                cleaned_part = part_clean.capitalize() + '.'
            else:
                cleaned_part = part_clean.capitalize()
            
            cleaned_parts.append(cleaned_part)
    
    result = " ".join(cleaned_parts)
    # Clean up spacing around punctuation
    result = result.replace(' .', '.').replace(' ,', ',')
    result = " ".join(result.split())  # Remove extra spaces
    
    return result


def _parse_music_response(response: str, destination: str, location_genres: List[str]) -> List[Dict[str, Any]]:
    """Parse LLM response and extract structured music recommendations."""
    
    recommendations = []
    
    # Remove markdown formatting from entire response first
    response = _strip_markdown(response)
    
    # Common patterns to extract songs
    # Look for song title patterns (quoted, numbered lists, etc.)
    lines = response.split('\n')
    current_song = {}
    
    for line in lines:
        # Remove markdown and clean line
        line = _strip_markdown(line.strip())
        if not line:
            if current_song:
                recommendations.append(current_song)
                current_song = {}
            continue
        
        # Pattern 1: "song" by artist or **"song"** by artist
        # This handles cases like: . **"austin" by the Allman Brothers**
        if ' by ' in line.lower():
            # Extract title and artist from "title" by artist format
            parts = line.split(' by ', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                artist = parts[1].strip()
                
                # Remove quotes, markdown, and numbering from title
                title = title.strip('"\'')
                title = title.strip('. -–—•1234567890)')
                # Remove any leading numbering like "1.", "2.", etc.
                title = re.sub(r'^\d+[\.\)]\s*', '', title)
                # Remove any remaining quotes
                title = title.strip('"\'')
                
                if title and artist:
                    if current_song:
                        recommendations.append(current_song)
                    current_song = {
                        "destination": destination,
                        "title": _clean_song_name(title),
                        "artist": _clean_artist_name(artist)
                    }
                    continue
        
        # Pattern 2: Look for song title patterns with keywords
        if any(keyword in line.lower() for keyword in ["song:", "track:", "title:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]):
            if current_song:
                recommendations.append(current_song)
            current_song = {"destination": destination}
            
            # Extract song title (remove numbering, keywords)
            title = line
            for prefix in ["song:", "track:", "title:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12."]:
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix):].strip()
                    break
            
            # Remove quotes and markdown if present
            title = title.strip('"\'')
            title = _strip_markdown(title)
            # Clean the title
            current_song["title"] = _clean_song_name(title)
        
        # Pattern 3: Look for artist
        elif any(keyword in line.lower() for keyword in ["artist:", "by:", "performed by:"]):
            artist = line
            for prefix in ["artist:", "by:", "performed by:"]:
                if artist.lower().startswith(prefix.lower()):
                    artist = artist[len(prefix):].strip()
                    break
            # Clean the artist name
            artist = _strip_markdown(artist)
            current_song["artist"] = _clean_artist_name(artist)
        
        # Pattern 4: Look for genre
        elif "genre:" in line.lower():
            genre = line.split(":")[1].strip() if ":" in line else line
            # Clean genre name
            genre = _strip_markdown(genre)
            genre = genre.strip().title()
            current_song["genre"] = genre
        
        # Pattern 5: Look for mood/energy
        elif any(keyword in line.lower() for keyword in ["mood:", "energy:", "vibe:"]):
            mood = line.split(":")[1].strip() if ":" in line else line
            # Clean mood name
            mood = _strip_markdown(mood)
            mood = mood.strip().title()
            current_song["mood"] = mood
    
    # Add last song if exists
    if current_song:
        recommendations.append(current_song)
    
    # If parsing didn't work well, use fallback extraction
    if len(recommendations) < 3:
        return _extract_songs_from_text(response, destination, location_genres)
    
    # Enhance recommendations with missing fields and clean all fields
    for rec in recommendations:
        # Clean title and artist if they exist
        if "title" in rec:
            rec["title"] = _clean_song_name(rec["title"])
        if "artist" in rec:
            rec["artist"] = _clean_artist_name(rec["artist"])
        
        if "genre" not in rec:
            rec["genre"] = location_genres[0] if location_genres else "Pop"
        else:
            rec["genre"] = _strip_markdown(rec["genre"]).strip().title()
        
        if "mood" not in rec:
            rec["mood"] = "Upbeat"
        else:
            rec["mood"] = _strip_markdown(rec["mood"]).strip().title()
        
        if "why" not in rec:
            rec["why"] = f"Perfect vibe for {destination}"
        else:
            rec["why"] = _strip_markdown(rec["why"]).strip()
        
        if "best_for" not in rec:
            rec["best_for"] = "Instagram Stories & Reels"
        else:
            rec["best_for"] = _strip_markdown(rec["best_for"]).strip()
    
    return recommendations[:12]  # Limit to 12 songs


def _extract_songs_from_text(text: str, destination: str, location_genres: List[str]) -> List[Dict[str, Any]]:
    """Extract song information from unstructured text."""
    
    recommendations = []
    
    # Remove markdown formatting first
    text = _strip_markdown(text)
    
    # Look for common song patterns in the text
    # This is a fallback if structured parsing fails
    lines = text.split('\n')
    
    for line in lines:
        line = _strip_markdown(line.strip())
        if not line:
            continue
            
        # Look for lines that might contain song information
        # Pattern: "song" by artist or song - artist or song – artist
        if " by " in line.lower():
            # Find " by " case-insensitive
            idx = line.lower().find(" by ")
            if idx >= 0:
                title = line[:idx].strip()
                artist = line[idx+4:].strip()
                
                # Remove quotes, numbering, and markdown
                title = title.strip('"\'')
                title = re.sub(r'^\d+[\.\)]\s*', '', title)  # Remove numbering
                title = title.strip('. -–—•')
                title = title.strip('"\'')  # Remove any remaining quotes
                artist = artist.strip('. -–—•')
                
                # Clean the title and artist
                title = _clean_song_name(title)
                artist = _clean_artist_name(artist)
                
                if title and artist and len(title) > 2:
                    recommendations.append({
                        "title": title,
                        "artist": artist,
                        "genre": location_genres[0] if location_genres else "Pop",
                        "mood": "Upbeat",
                        "why": f"Great vibe for {destination}",
                        "best_for": "Social Media Posts",
                        "destination": destination
                    })
        elif " - " in line or " – " in line:
            # Try different separators
            if " - " in line:
                parts = line.split(" - ", 1)
            elif " – " in line:
                parts = line.split(" – ", 1)
            else:
                continue
            
            if len(parts) >= 2:
                title = parts[0].strip()
                artist = parts[1].strip()
                
                # Remove quotes, numbering, and markdown
                title = title.strip('"\'')
                title = re.sub(r'^\d+[\.\)]\s*', '', title)
                title = title.strip('. -–—•1234567890.,;:!?()[]{}')
                title = title.strip('"\'')  # Remove any remaining quotes
                artist = artist.strip('"\'.,;:!?()[]{}')
                
                # Clean the title and artist
                title = _clean_song_name(title)
                artist = _clean_artist_name(artist)
                
                if title and artist and len(title) > 2:
                    recommendations.append({
                        "title": title,
                        "artist": artist,
                        "genre": location_genres[0] if location_genres else "Pop",
                        "mood": "Upbeat",
                        "why": f"Great vibe for {destination}",
                        "best_for": "Social Media Posts",
                        "destination": destination
                    })
    
    # If still no songs, use location-based defaults
    if not recommendations:
        return _get_default_songs_for_location(destination, location_genres)
    
    # Clean all recommendations
    for rec in recommendations:
        rec["title"] = _clean_song_name(rec["title"])
        rec["artist"] = _clean_artist_name(rec["artist"])
        rec["genre"] = rec["genre"].strip().title()
        rec["mood"] = rec["mood"].strip().title()
    
    return recommendations[:12]


def _get_default_songs_for_location(destination: str, location_genres: List[str]) -> List[Dict[str, Any]]:
    """Get default song recommendations based on location and genres."""
    
    destination_lower = destination.lower()
    genre = location_genres[0] if location_genres else "Pop"
    
    # Location-specific default songs (all properly formatted)
    default_songs = {
        "austin": [
            {"title": "Texas Sun", "artist": "Khruangbin & Leon Bridges", "genre": "Indie", "mood": "Chill", "why": "Austin vibe classic", "best_for": "Instagram Stories"},
            {"title": "God Blessed Texas", "artist": "Little Texas", "genre": "Country", "mood": "Energetic", "why": "Texas anthem", "best_for": "TikTok"},
            {"title": "South Side", "artist": "Moby", "genre": "Electronic", "mood": "Upbeat", "why": "Great for travel content", "best_for": "Reels"},
            {"title": "Austin", "artist": "Blake Shelton", "genre": "Country", "mood": "Upbeat", "why": "Perfect Austin song", "best_for": "Instagram Stories"},
            {"title": "Deep In The Heart Of Texas", "artist": "George Strait", "genre": "Country", "mood": "Chill", "why": "Texas classic", "best_for": "Reels"},
        ],
        "california": [
            {"title": "California Love", "artist": "2Pac ft. Dr. Dre", "genre": "Hip-Hop", "mood": "Energetic", "why": "California classic", "best_for": "Instagram Stories"},
            {"title": "Hotel California", "artist": "Eagles", "genre": "Rock", "mood": "Chill", "why": "Iconic California song", "best_for": "Photo Slideshows"},
            {"title": "California Gurls", "artist": "Katy Perry", "genre": "Pop", "mood": "Upbeat", "why": "Fun California vibe", "best_for": "TikTok"},
            {"title": "California Dreamin'", "artist": "The Mamas & The Papas", "genre": "Folk Rock", "mood": "Chill", "why": "Classic California vibe", "best_for": "Reels"},
            {"title": "California", "artist": "Phantom Planet", "genre": "Rock", "mood": "Upbeat", "why": "Perfect for California posts", "best_for": "Instagram Stories"},
        ],
        "new york": [
            {"title": "Empire State Of Mind", "artist": "Jay-Z & Alicia Keys", "genre": "Hip-Hop", "mood": "Inspiring", "why": "NYC anthem", "best_for": "Instagram Stories"},
            {"title": "New York, New York", "artist": "Frank Sinatra", "genre": "Jazz", "mood": "Classic", "why": "Timeless NYC song", "best_for": "Reels"},
            {"title": "Welcome To New York", "artist": "Taylor Swift", "genre": "Pop", "mood": "Upbeat", "why": "Perfect for travel posts", "best_for": "TikTok"},
            {"title": "New York State Of Mind", "artist": "Billy Joel", "genre": "Rock", "mood": "Chill", "why": "NYC classic", "best_for": "Instagram Stories"},
            {"title": "Theme From New York, New York", "artist": "Frank Sinatra", "genre": "Jazz", "mood": "Classic", "why": "Iconic NYC song", "best_for": "Reels"},
        ],
        "miami": [
            {"title": "Despacito", "artist": "Luis Fonsi & Daddy Yankee", "genre": "Latin", "mood": "Energetic", "why": "Miami Latin vibe", "best_for": "Instagram Stories"},
            {"title": "Conga", "artist": "Gloria Estefan", "genre": "Latin", "mood": "Energetic", "why": "Miami classic", "best_for": "TikTok"},
            {"title": "Mi Gente", "artist": "J Balvin & Willy William", "genre": "Reggaeton", "mood": "Upbeat", "why": "Perfect for Miami", "best_for": "Reels"},
            {"title": "Gasolina", "artist": "Daddy Yankee", "genre": "Reggaeton", "mood": "Energetic", "why": "Miami party vibe", "best_for": "Instagram Stories"},
            {"title": "La Bicicleta", "artist": "Carlos Vives & Shakira", "genre": "Latin", "mood": "Upbeat", "why": "Great for Miami posts", "best_for": "TikTok"},
        ],
        "texas": [
            {"title": "Texas Sun", "artist": "Khruangbin & Leon Bridges", "genre": "Indie", "mood": "Chill", "why": "Texas vibe classic", "best_for": "Instagram Stories"},
            {"title": "God Blessed Texas", "artist": "Little Texas", "genre": "Country", "mood": "Energetic", "why": "Texas anthem", "best_for": "TikTok"},
            {"title": "All My Ex's Live In Texas", "artist": "George Strait", "genre": "Country", "mood": "Upbeat", "why": "Texas country classic", "best_for": "Reels"},
            {"title": "The Yellow Rose Of Texas", "artist": "Mitch Miller", "genre": "Country", "mood": "Chill", "why": "Texas tradition", "best_for": "Instagram Stories"},
        ],
        "los angeles": [
            {"title": "California Love", "artist": "2Pac ft. Dr. Dre", "genre": "Hip-Hop", "mood": "Energetic", "why": "LA classic", "best_for": "Instagram Stories"},
            {"title": "I Love LA", "artist": "Randy Newman", "genre": "Pop", "mood": "Upbeat", "why": "Perfect LA anthem", "best_for": "TikTok"},
            {"title": "California", "artist": "Phantom Planet", "genre": "Rock", "mood": "Upbeat", "why": "Great for LA posts", "best_for": "Reels"},
            {"title": "Malibu", "artist": "Miley Cyrus", "genre": "Pop", "mood": "Chill", "why": "LA beach vibe", "best_for": "Instagram Stories"},
        ],
    }
    
    # Find matching location
    for location, songs in default_songs.items():
        if location in destination_lower:
            for song in songs:
                song["destination"] = destination
                # Ensure all fields are properly formatted
                song["title"] = _clean_song_name(song["title"])
                song["artist"] = _clean_artist_name(song["artist"])
                song["genre"] = song["genre"].title()
                song["mood"] = song["mood"].title()
            return songs
    
    # Generic travel songs (properly formatted)
    generic_songs = [
        {"title": "On Top Of The World", "artist": "Imagine Dragons", "genre": genre, "mood": "Inspiring", "why": "Perfect travel anthem", "best_for": "Instagram Stories", "destination": destination},
        {"title": "Good Life", "artist": "OneRepublic", "genre": "Pop", "mood": "Upbeat", "why": "Great for vacation vibes", "best_for": "Reels", "destination": destination},
        {"title": "Adventure Of A Lifetime", "artist": "Coldplay", "genre": "Pop Rock", "mood": "Energetic", "why": "Perfect for travel content", "best_for": "TikTok", "destination": destination},
        {"title": "I Gotta Feeling", "artist": "Black Eyed Peas", "genre": "Pop", "mood": "Upbeat", "why": "Fun vacation vibe", "best_for": "Instagram Stories", "destination": destination},
        {"title": "Walking On Sunshine", "artist": "Katrina & The Waves", "genre": "Pop", "mood": "Upbeat", "why": "Perfect for travel posts", "best_for": "Reels", "destination": destination},
        {"title": "Happy", "artist": "Pharrell Williams", "genre": "Pop", "mood": "Upbeat", "why": "Great vacation vibe", "best_for": "TikTok", "destination": destination},
    ]
    
    # Clean all generic songs
    for song in generic_songs:
        song["title"] = _clean_song_name(song["title"])
        song["artist"] = _clean_artist_name(song["artist"])
        song["genre"] = song["genre"].title()
        song["mood"] = song["mood"].title()
    
    return generic_songs


def _get_fallback_music_recommendations(destination: str, location_genres: List[str], season: Optional[str] = None) -> Dict[str, Any]:
    """Get fallback music recommendations when LLM fails."""
    
    recommendations = _get_default_songs_for_location(destination, location_genres)
    
    return {
        "status": "success",
        "destination": destination,
        "location_genres": location_genres,
        "season": season,
        "mood": "vibrant",
        "recommendations": recommendations,
        "raw_llm_response": f"Fallback recommendations for {destination}"
    }

