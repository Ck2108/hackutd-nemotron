"""
Nemotron LLM client with OpenAI-compatible API support and fallbacks.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NemotronClient:
    """OpenAI-compatible client for Nemotron with robust fallbacks."""
    
    def __init__(self):
        self.api_base = os.getenv("LLM_API_BASE", "")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "nvidia/nemotron-4-340b-reward")
        self.provider = os.getenv("LLM_PROVIDER", "openai_compatible")
        self.use_mocks = os.getenv("USE_MOCKS", "false").lower() == "true"
        
        # Check if we have valid API configuration
        self.has_api_config = bool(self.api_base and self.api_key)
        
        if not self.has_api_config:
            logger.info("No LLM API configuration found, using fallback responses")
    
    def get_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Get a text completion from Nemotron or fallback."""
        if self.use_mocks or not self.has_api_config:
            return self._get_fallback_completion(prompt)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            # Handle both endpoint formats
            if self.api_base.endswith('/chats/complete') or self.api_base.endswith('/chat/completions'):
                endpoint = self.api_base
            else:
                endpoint = f"{self.api_base.rstrip('/')}/chat/completions"
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return self._get_fallback_completion(prompt)
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._get_fallback_completion(prompt)
    
    def get_json_completion(self, prompt: str, schema: Dict[str, Any], max_tokens: int = 2000) -> Dict[str, Any]:
        """Get structured JSON output from Nemotron with schema validation."""
        if self.use_mocks or not self.has_api_config:
            return self._get_fallback_json(prompt, schema)
        
        # Add JSON schema instructions to prompt
        schema_prompt = f"""
{prompt}

Please respond with valid JSON matching this exact schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no other text or markdown formatting.
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that always responds with valid JSON."},
                    {"role": "user", "content": schema_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3
            }
            
            # Handle both endpoint formats
            if self.api_base.endswith('/chats/complete') or self.api_base.endswith('/chat/completions'):
                endpoint = self.api_base
            else:
                endpoint = f"{self.api_base.rstrip('/')}/chat/completions"
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse JSON from response
                try:
                    # Clean the response (remove markdown formatting if present)
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response: {content}")
                    return self._get_fallback_json(prompt, schema)
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return self._get_fallback_json(prompt, schema)
                
        except Exception as e:
            logger.error(f"LLM JSON API call failed: {e}")
            return self._get_fallback_json(prompt, schema)
    
    def _get_fallback_completion(self, prompt: str) -> str:
        """Deterministic fallback for text completions."""
        if "planning" in prompt.lower() or "itinerary" in prompt.lower():
            # Extract origin and destination from prompt
            import re
            origin_match = re.search(r'Origin:\s*([^\n]+)', prompt)
            destination_match = re.search(r'Destination:\s*([^\n]+)', prompt)
            
            origin = origin_match.group(1).strip() if origin_match else "your origin"
            destination = destination_match.group(1).strip() if destination_match else "your destination"
            
            return f"""Based on your request for a trip from {origin} to {destination}, I recommend:

1. Transportation: Driving (approximately 3-4 hours, ~$40-60 in gas)
2. Lodging: Mid-range hotel in downtown {destination} ($120-150/night)
3. Activities: Restaurants, attractions, and local venues
4. Budget allocation: Transport $50, Lodging $300, Activities $450

This plan maximizes your interests while staying within budget."""
        
        elif "weather" in prompt.lower():
            return "The weather forecast shows sunny conditions with highs in the 70s and minimal chance of rain."
        
        elif "reasoning" in prompt.lower() or "decision" in prompt.lower():
            return "Selected based on proximity to hotel, alignment with interests, and budget constraints."
        
        else:
            return "I'll help you plan your trip with the available information and preferences."
    
    def _get_fallback_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic fallback for JSON completions based on schema."""
        # Planning response fallback - extract values from prompt
        if "steps" in schema.get("properties", {}):
            # Extract origin, destination, and interests from prompt
            import re
            origin_match = re.search(r'Origin:\s*([^\n]+)', prompt)
            destination_match = re.search(r'Destination:\s*([^\n]+)', prompt)
            interests_match = re.search(r'Interests:\s*([^\n]+)', prompt)
            budget_match = re.search(r'Total Budget:\s*\$?([\d.]+)', prompt)
            
            origin = origin_match.group(1).strip() if origin_match else "Unknown"
            destination = destination_match.group(1).strip() if destination_match else "Unknown"
            interests_str = interests_match.group(1).strip() if interests_match else "None specified"
            budget = float(budget_match.group(1)) if budget_match else 800.0
            
            # Parse interests
            if interests_str and interests_str.lower() != "none specified":
                interests = [i.strip() for i in interests_str.split(',')]
            else:
                interests = ["restaurants", "attractions"]
            
            # Create steps with extracted values
            steps = [
                {
                    "phase": "transport",
                    "description": f"Find driving directions from {origin} to {destination}",
                    "tool": "maps.find_directions",
                    "params": {"origin": origin, "destination": destination}
                },
                {
                    "phase": "lodging",
                    "description": f"Search for hotels in {destination}",
                    "tool": "hotels.search",
                    "params": {"city": destination, "max_price": min(200, budget * 0.3), "limit": 5}
                },
                {
                    "phase": "activities",
                    "description": f"Check weather forecast for {destination}",
                    "tool": "weather.forecast",
                    "params": {"city": destination}
                }
            ]
            
            # Add activity searches based on interests (limit to first 2)
            for interest in interests[:2]:
                steps.append({
                    "phase": "activities",
                    "description": f"Search for {interest} in {destination}",
                    "tool": "places.search",
                    "params": {"query": interest, "near": destination, "limit": 10}
                })
            
            steps.append({
                "phase": "synthesis",
                "description": "Create final itinerary",
                "tool": "synthesis.none",
                "params": {}
            })
            
            # Calculate budget allocations
            # Estimate transport: if long distance (>500 miles), use flying estimate, else driving
            # We can't know exact distance here, so use conservative estimate
            # For long trips, assume flying; for short trips, assume driving
            transport_est = min(50.0, budget * 0.1)  # Default to driving estimate
            # If budget is large (>$2000), might be long distance, estimate higher
            if budget > 2000:
                transport_est = min(800.0, budget * 0.2)  # Flying estimate
            
            remaining = budget - transport_est
            lodging_target = remaining * 0.6
            activities_buffer = max(150.0, budget * 0.2)
            
            return {
                "steps": steps,
                "allocations": {
                    "transport": transport_est,
                    "lodging_target": lodging_target,
                    "activities_buffer": activities_buffer
                },
                "reasoning": f"Driving from {origin} to {destination}. Allocated budget: Transport ${transport_est}, Lodging ${lodging_target}, Activities ${activities_buffer}."
            }
        
        # Generic fallback - return schema with default values
        return self._generate_schema_defaults(schema)
    
    def _generate_schema_defaults(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default values based on JSON schema."""
        result = {}
        properties = schema.get("properties", {})
        
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            
            if prop_type == "string":
                result[key] = prop.get("default", "")
            elif prop_type == "number":
                result[key] = prop.get("default", 0.0)
            elif prop_type == "integer":
                result[key] = prop.get("default", 0)
            elif prop_type == "boolean":
                result[key] = prop.get("default", False)
            elif prop_type == "array":
                result[key] = prop.get("default", [])
            elif prop_type == "object":
                result[key] = prop.get("default", {})
        
        return result


# Global client instance
llm_client = NemotronClient()


def get_completion(prompt: str, max_tokens: int = 1000) -> str:
    """Get text completion from Nemotron."""
    return llm_client.get_completion(prompt, max_tokens)


def get_json_completion(prompt: str, schema: Dict[str, Any], max_tokens: int = 2000) -> Dict[str, Any]:
    """Get structured JSON completion from Nemotron."""
    return llm_client.get_json_completion(prompt, schema, max_tokens)
