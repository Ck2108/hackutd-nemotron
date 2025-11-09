# How to Update Your .env File with Real API Key

## Current .env File Structure:
```bash
# Nemotron LLM Configuration
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=your_nvidia_nim_api_key_here    ← CHANGE THIS
LLM_MODEL=nvidia/nemotron-4-340b-reward     ← CHANGE THIS  
LLM_PROVIDER=openai_compatible

# Mock Data Configuration
USE_MOCKS=true                              ← CHANGE THIS

# Optional: External API Keys (when USE_MOCKS=false)
GOOGLE_MAPS_API_KEY=your_google_maps_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
```

## What to Change:

### 1. Replace API Key (Line 3):
**From:**
```bash
LLM_API_KEY=your_nvidia_nim_api_key_here
```
**To:**
```bash
LLM_API_KEY=nvapi-your-actual-key-from-nvidia-build
```

### 2. Update Model (Line 4):
**From:**
```bash
LLM_MODEL=nvidia/nemotron-4-340b-reward
```
**To:**
```bash
LLM_MODEL=nvidia/nemotron-nano-9b-v2
```

### 3. Enable Live Mode (Line 8):
**From:**
```bash
USE_MOCKS=true
```
**To:**
```bash
USE_MOCKS=false
```

## Final .env File Should Look Like:
```bash
# Nemotron LLM Configuration
LLM_API_BASE=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-actual-key-here
LLM_MODEL=nvidia/nemotron-nano-9b-v2
LLM_PROVIDER=openai_compatible

# Mock Data Configuration
USE_MOCKS=false

# Optional: External API Keys (when USE_MOCKS=false)
GOOGLE_MAPS_API_KEY=your_google_maps_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
```

## ⚠️ Security Note:
- Keep your API key private
- Don't share your .env file
- The .env file is automatically ignored by git
