// API Base URL
const API_BASE_URL = 'http://localhost:5001/api';

// Global state
let currentItinerary = null;
let currentUserRequest = null;
let map = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    const endDate = new Date(nextWeek);
    endDate.setDate(nextWeek.getDate() + 2);
    
    document.getElementById('start-date').value = nextWeek.toISOString().split('T')[0];
    document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
    
    // Form submission
    document.getElementById('trip-form').addEventListener('submit', handleFormSubmit);
    
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
    
    // Download buttons
    document.getElementById('download-json').addEventListener('click', downloadJSON);
    document.getElementById('download-calendar').addEventListener('click', downloadCalendar);
});

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(e.target);
    const interests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(cb => cb.value);
    
    const requestData = {
        origin: formData.get('origin'),
        destination: formData.get('destination'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        travelers: parseInt(formData.get('travelers')),
        budget_total: parseFloat(formData.get('budget_total')),
        interests: interests,
        use_mocks: document.getElementById('use-mocks').checked,
        weather_mode: document.getElementById('weather-mode').value
    };
    
    // Validate
    if (!requestData.origin || !requestData.destination) {
        showStatus('Please provide both origin and destination', 'error');
        return;
    }
    
    if (new Date(requestData.start_date) >= new Date(requestData.end_date)) {
        showStatus('End date must be after start date', 'error');
        return;
    }
    
    // Hide welcome message and show loading
    document.getElementById('welcome-message').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    
    // Update progress
    updateProgress(20, '🧠 Creating execution plan...');
    
    try {
        // Make API call
        const response = await fetch(`${API_BASE_URL}/plan-trip`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to plan trip');
        }
        
        const result = await response.json();
        
        // Validate result structure
        if (!result.itinerary) {
            throw new Error('Invalid response: missing itinerary data');
        }
        
        if (!result.user_request) {
            throw new Error('Invalid response: missing user request data');
        }
        
        // Store results
        currentItinerary = result.itinerary;
        currentUserRequest = result.user_request;
        
        // Log for debugging
        console.log('Trip planned successfully:', {
            items: result.itinerary.items?.length || 0,
            map_points: result.itinerary.map_points?.length || 0,
            budget: result.itinerary.budget_breakdown ? 'present' : 'missing'
        });
        
        // Update progress
        updateProgress(100, '✅ Complete!');
        
        // Display results
        setTimeout(() => {
            document.getElementById('loading').classList.add('hidden');
            try {
                displayResults(result);
            } catch (displayError) {
                console.error('Error displaying results:', displayError);
                showStatus(`Error displaying results: ${displayError.message}`, 'error');
            }
        }, 500);
        
    } catch (error) {
        console.error('Error planning trip:', error);
        console.error('Error details:', error);
        showStatus(`Error: ${error.message || 'Failed to plan trip. Please check console for details.'}`, 'error');
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('welcome-message').classList.remove('hidden');
        
        // Show error details in console
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
    }
}

// Update progress bar
function updateProgress(percentage, message) {
    document.getElementById('progress-bar').style.width = `${percentage}%`;
    document.getElementById('loading-message').textContent = message;
}

// Display results
function displayResults(result) {
    const itinerary = result.itinerary;
    const userRequest = result.user_request;
    
    // Store results globally for later use
    currentItinerary = itinerary;
    currentUserRequest = userRequest;
    
    // Show results container
    document.getElementById('results').classList.remove('hidden');
    
    // Display trip summary
    displayTripSummary(userRequest);
    
    // Display schedule
    displaySchedule(itinerary);
    
    // Display budget
    displayBudget(itinerary);
    
    // Don't initialize map yet - wait until map tab is clicked
    // This prevents map initialization issues when tab is hidden
    
    // Display clothing suggestions
    displayClothing(itinerary);
    
    // Display music recommendations
    displayMusic(itinerary);
    
    // Display city history
    displayCityHistory(itinerary.city_history);
    
    // Display agent log
    displayAgentLog(result.agent_state);
    
    // Switch to schedule tab
    switchTab('schedule');
}

// Display trip summary
function displayTripSummary(userRequest) {
    const startDate = new Date(userRequest.start_date);
    const endDate = new Date(userRequest.end_date);
    const interests = userRequest.interests.slice(0, 3).join(', ') + 
                     (userRequest.interests.length > 3 ? '...' : '');
    
    document.getElementById('trip-summary').innerHTML = `
        <h2 class="text-2xl font-bold mb-4 text-gray-800">
            🎯 Your Trip: ${userRequest.origin} → ${userRequest.destination}
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
                <span class="font-semibold">📅 Dates:</span>
                <div>${startDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - 
                     ${endDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</div>
            </div>
            <div>
                <span class="font-semibold">👥 Travelers:</span>
                <div>${userRequest.travelers}</div>
            </div>
            <div>
                <span class="font-semibold">💰 Budget:</span>
                <div>$${userRequest.budget_total.toFixed(0)}</div>
            </div>
            <div>
                <span class="font-semibold">🎯 Interests:</span>
                <div>${interests}</div>
            </div>
        </div>
    `;
}

// Display daily schedule
function displaySchedule(itinerary) {
    if (!itinerary || !itinerary.items || itinerary.items.length === 0) {
        document.getElementById('schedule-content').innerHTML = 
            '<div class="p-4"><p class="text-gray-600">No schedule items available. The itinerary may still be processing.</p></div>';
        return;
    }
    
    // Group items by day
    const days = {};
    itinerary.items.forEach(item => {
        const dayStr = new Date(item.day).toLocaleDateString('en-US', { 
            month: 'long', 
            day: 'numeric', 
            year: 'numeric' 
        });
        if (!days[dayStr]) {
            days[dayStr] = [];
        }
        days[dayStr].push(item);
    });
    
    // Sort days
    const sortedDays = Object.keys(days).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    let html = '';
    sortedDays.forEach(day => {
        html += `<h3 class="text-xl font-bold mt-6 mb-4 text-gray-800">📅 ${day}</h3>`;
        days[day].forEach(item => {
            const link = item.link ? `<a href="${item.link}" target="_blank" class="text-blue-600 hover:underline">${item.title}</a>` : item.title;
            html += `
                <div class="border border-gray-200 rounded-lg p-4 mb-4">
                    <div class="grid grid-cols-3 gap-4">
                        <div class="font-semibold text-gray-700">${item.time}</div>
                        <div class="col-span-2">
                            <div class="font-semibold text-lg text-gray-800">${link}</div>
                            ${item.address ? `<div class="text-sm text-gray-600 mt-1">📍 ${item.address}</div>` : ''}
                            ${item.notes ? `<div class="text-sm text-gray-600 mt-1">ℹ️ ${item.notes}</div>` : ''}
                        </div>
                        ${item.est_cost > 0 ? `<div class="text-right font-semibold text-green-600">💰 $${item.est_cost.toFixed(2)}</div>` : ''}
                    </div>
                </div>
            `;
        });
    });
    
    document.getElementById('schedule-content').innerHTML = html;
}

// Display budget breakdown
function displayBudget(itinerary) {
    if (!itinerary || !itinerary.budget_breakdown) {
        document.getElementById('budget-content').innerHTML = 
            '<div class="p-4"><p class="text-gray-600">No budget information available. The itinerary may still be processing.</p></div>';
        return;
    }
    
    const budget = itinerary.budget_breakdown;
    
    const total = budget.total_spent + budget.remaining;
    const utilization = total > 0 ? (budget.total_spent / total * 100) : 0;
    
    let html = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="p-4 rounded-lg text-center" style="background-color: #f0f8e6;">
                <div class="text-2xl font-bold" style="color: #76B900;">$${budget.transport.toFixed(2)}</div>
                <div class="text-sm text-gray-600 mt-1">🚗 Transport</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg text-center">
                <div class="text-2xl font-bold text-green-600">$${budget.lodging.toFixed(2)}</div>
                <div class="text-sm text-gray-600 mt-1">🏨 Lodging</div>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg text-center">
                <div class="text-2xl font-bold text-purple-600">$${budget.activities.toFixed(2)}</div>
                <div class="text-sm text-gray-600 mt-1">🎯 Activities</div>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg text-center">
                <div class="text-2xl font-bold text-gray-600">$${budget.remaining.toFixed(2)}</div>
                <div class="text-sm text-gray-600 mt-1">💵 Remaining</div>
            </div>
        </div>
        
        <div class="mb-6">
            <h4 class="text-lg font-semibold mb-2 text-gray-800">Budget Utilization</h4>
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="h-2.5 rounded-full transition-all" style="width: ${Math.min(100, utilization)}%; background-color: #76B900;"></div>
            </div>
            <div class="text-sm text-gray-600 mt-2">${utilization.toFixed(1)}% of budget used</div>
        </div>
        
        <div>
            <h4 class="text-lg font-semibold mb-2 text-gray-800">Detailed Breakdown</h4>
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Percentage</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Transport</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${budget.transport.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${budget.total_spent > 0 ? (budget.transport / budget.total_spent * 100).toFixed(1) : 0}%</td>
                    </tr>
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Lodging</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${budget.lodging.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${budget.total_spent > 0 ? (budget.lodging / budget.total_spent * 100).toFixed(1) : 0}%</td>
                    </tr>
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Activities</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${budget.activities.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${budget.total_spent > 0 ? (budget.activities / budget.total_spent * 100).toFixed(1) : 0}%</td>
                    </tr>
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Remaining</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${budget.remaining.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${total > 0 ? (budget.remaining / total * 100).toFixed(1) : 0}%</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('budget-content').innerHTML = html;
}

// Display map
function displayMap(itinerary) {
    if (!itinerary || !itinerary.map_points || itinerary.map_points.length === 0) {
        document.getElementById('map-content').innerHTML = 
            '<div class="p-6"><p class="text-gray-600">No map points available. The itinerary may still be processing or no locations were found.</p></div>';
        return;
    }
    
    // Filter out points without valid coordinates
    const validPoints = itinerary.map_points.filter(p => {
        if (!p) return false;
        const lat = p.lat || p.latitude;
        const lng = p.lng || p.longitude;
        return lat != null && lng != null && !isNaN(parseFloat(lat)) && !isNaN(parseFloat(lng));
    });
    
    if (validPoints.length === 0) {
        document.getElementById('map-content').innerHTML = 
            '<div class="p-6"><p class="text-gray-600">No valid map points with coordinates available.</p><p class="text-sm text-gray-500 mt-2">This might happen if location data is missing.</p></div>';
        return;
    }
    
    // Clear existing map if it exists
    if (map) {
        map.remove();
        map = null;
    }
    
    // Calculate center - handle both lat/lng and latitude/longitude formats
    const centerLat = validPoints.reduce((sum, p) => {
        const lat = p.lat || p.latitude || 0;
        return sum + parseFloat(lat);
    }, 0) / validPoints.length;
    
    const centerLng = validPoints.reduce((sum, p) => {
        const lng = p.lng || p.longitude || 0;
        return sum + parseFloat(lng);
    }, 0) / validPoints.length;
    
    // Initialize map - use setTimeout to ensure DOM is ready
    setTimeout(() => {
        const mapElement = document.getElementById('map');
        if (!mapElement) {
            console.error('Map element not found');
            return;
        }
        
        // Clear any existing content
        mapElement.innerHTML = '';
        
        try {
            map = L.map('map').setView([centerLat, centerLng], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(map);
            
            // Add markers
            validPoints.forEach(point => {
                // Handle both lat/lng and latitude/longitude formats
                const lat = parseFloat(point.lat || point.latitude);
                const lng = parseFloat(point.lng || point.longitude);
                
                if (isNaN(lat) || isNaN(lng)) {
                    console.warn('Invalid coordinates for point:', point);
                    return; // Skip invalid points
                }
                
                const isHotel = point.type === 'hotel';
                
                // Create custom colored marker
                const markerColor = isHotel ? 'red' : 'blue';
                const markerIcon = isHotel ? '🏠' : '⭐';
                
                // Create a simple colored circle marker
                const icon = L.divIcon({
                    html: `<div style="background-color: ${markerColor}; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 18px;">${markerIcon}</div>`,
                    className: 'custom-marker',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                    popupAnchor: [0, -16]
                });
                
                const popupHtml = `<b>${point.name || 'Unknown'}</b>${point.link ? `<br><a href="${point.link}" target="_blank" style="color: blue;">More Info</a>` : ''}`;
                
                L.marker([lat, lng], { icon: icon })
                    .addTo(map)
                    .bindPopup(popupHtml);
            });
            
            // Trigger map resize after a short delay to ensure proper rendering
            setTimeout(() => {
                if (map) {
                    map.invalidateSize();
                }
            }, 100);
            
        } catch (error) {
            console.error('Error initializing map:', error);
            document.getElementById('map-content').innerHTML = 
                `<div class="p-6"><p class="text-red-600">Error loading map: ${error.message}</p></div>`;
        }
    }, 100);
    
    // Update legend
    const activityCount = validPoints.filter(p => p.type === 'activity').length;
    const hotelCount = validPoints.filter(p => p.type === 'hotel').length;
    document.getElementById('map-legend').innerHTML = `
        <div class="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 class="font-semibold mb-2 text-gray-800">Map Legend</h4>
            <div class="flex items-center space-x-4 text-sm">
                <div class="flex items-center">
                    <span class="text-red-600 mr-2">🏠</span>
                    <span>Red markers = Hotel</span>
                </div>
                <div class="flex items-center">
                    <span class="text-blue-600 mr-2">⭐</span>
                    <span>Blue markers = Activities</span>
                </div>
            </div>
            <div class="mt-2 text-sm text-gray-600">
                📍 Total Locations: ${validPoints.length} | 🏨 Hotels: ${hotelCount} | 🎯 Activities: ${activityCount}
            </div>
        </div>
    `;
}

// Display clothing suggestions
function displayClothing(itinerary) {
    if (!itinerary.clothing_recommendations) {
        document.getElementById('clothing-content').innerHTML = 
            '<p class="text-gray-600">👔 Clothing suggestions are being generated based on your trip dates and destination...</p>';
        return;
    }
    
    const rec = itinerary.clothing_recommendations;
    
    let html = `
        <div class="mb-6 p-4 bg-blue-50 rounded-lg">
            <h3 class="text-xl font-bold mb-2 text-gray-800">🌤️ Weather-Based Clothing Recommendations</h3>
            <div class="text-sm text-gray-600">
                <strong>Weather:</strong> ${rec.weather_summary} | 
                <strong>Temperature:</strong> ${rec.temperature_range} | 
                <strong>Rain Chance:</strong> ${Math.round(rec.rain_chance * 100)}%
                ${rec.season ? ` | <strong>Season:</strong> ${rec.season}` : ''}
                ${rec.climate_zone ? ` | <strong>Climate:</strong> ${rec.climate_zone.replace('_', ' ')}` : ''}
            </div>
        </div>
    `;
    
    // Male suggestions
    if (rec.male_suggestions) {
        html += displayGenderSuggestions('Male', rec.male_suggestions);
    }
    
    // Female suggestions
    if (rec.female_suggestions) {
        html += displayGenderSuggestions('Female', rec.female_suggestions);
    }
    
    document.getElementById('clothing-content').innerHTML = html;
}

// Display gender-specific clothing suggestions
function displayGenderSuggestions(gender, suggestions) {
    let html = `<div class="mb-8"><h4 class="text-lg font-semibold mb-4 text-gray-800">👔 ${gender} Clothing Suggestions</h4>`;
    
    // Color palette
    if (suggestions.color_palette && suggestions.color_palette.length > 0) {
        html += '<h5 class="font-semibold mb-2 text-gray-700">🎨 Color Palette</h5><div class="grid grid-cols-3 md:grid-cols-6 gap-4 mb-6">';
        suggestions.color_palette.forEach(color => {
            const isDark = isDarkColor(color.hex);
            const textColor = isDark ? 'white' : 'black';
            const borderColor = isDark ? '#000000' : '#333333';
            html += `
                <div class="text-center">
                    <div class="color-swatch rounded-lg p-4 mb-2" style="background-color: ${color.hex}; color: ${textColor}; border-color: ${borderColor};">
                        ${color.name}
                    </div>
                    <div class="text-xs font-mono text-gray-600">${color.hex}</div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Outfit items
    html += '<h5 class="font-semibold mb-2 text-gray-700">👕 Recommended Outfit Items</h5>';
    html += '<div class="grid grid-cols-2 gap-4">';
    
    if (suggestions.outfit_items) {
        const items = suggestions.outfit_items;
        html += '<div><ul class="list-disc list-inside space-y-1 text-sm text-gray-600">';
        if (items.tops) items.tops.forEach(item => html += `<li>${item}</li>`);
        if (items.bottoms) items.bottoms.forEach(item => html += `<li>${item}</li>`);
        if (items.outerwear) items.outerwear.forEach(item => html += `<li>${item}</li>`);
        html += '</ul></div><div><ul class="list-disc list-inside space-y-1 text-sm text-gray-600">';
        if (items.footwear) items.footwear.forEach(item => html += `<li>${item}</li>`);
        if (items.accessories) items.accessories.forEach(item => html += `<li>${item}</li>`);
        if (suggestions.special_items) suggestions.special_items.forEach(item => html += `<li>${item}</li>`);
        html += '</ul></div>';
    }
    
    html += '</div>';
    
    // Style notes
    if (suggestions.style_notes) {
        html += `<div class="mt-4 p-4 bg-yellow-50 rounded-lg"><p class="text-sm text-gray-700">💡 ${suggestions.style_notes}</p></div>`;
    }
    
    html += '</div>';
    return html;
}

// Check if color is dark
function isDarkColor(hex) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance < 0.5;
}

// Display music recommendations
function displayMusic(itinerary) {
    if (!itinerary || !itinerary.music_recommendations) {
        document.getElementById('music-content').innerHTML = 
            '<p class="text-gray-600">🎵 Music recommendations are being generated based on your destination...</p>';
        return;
    }
    
    const musicRec = itinerary.music_recommendations;
    
    let html = `
        <div class="mb-6 p-4 bg-white border-2 border-gray-200 rounded-lg">
            <h3 class="text-2xl font-bold mb-2" style="color: #76B900;">🎵 Music Recommendations for ${musicRec.destination}</h3>
            <p class="text-gray-600">
                <strong>Popular Genres:</strong> ${musicRec.location_genres ? musicRec.location_genres.join(', ') : 'Various'} | 
                <strong>Season:</strong> ${musicRec.season ? musicRec.season : 'Any'} | 
                <strong>Mood:</strong> ${musicRec.mood}
            </p>
        </div>
    `;
    
    if (musicRec.songs && musicRec.songs.length > 0) {
        html += '<h4 class="text-lg font-semibold mb-4 text-gray-800">🎶 Recommended Songs</h4>';
        
        musicRec.songs.forEach((song) => {
            // Clean song title and artist name
            const cleanTitle = (song.title || '').trim();
            const cleanArtist = (song.artist || '').trim();
            
            // Remove any numbering or prefixes that might have been included
            const titleWithoutNumber = cleanTitle.replace(/^\d+[\.\)]\s*/, '').replace(/^[•\-\*]\s*/, '').trim();
            
            if (!titleWithoutNumber || !cleanArtist) {
                return; // Skip invalid songs
            }
            
            const searchQuery = `${cleanArtist} ${titleWithoutNumber}`.replace(/ /g, '+');
            const spotifyUrl = `https://open.spotify.com/search/${encodeURIComponent(searchQuery)}`;
            const youtubeUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(searchQuery)}`;
            
            html += `
                <div class="border border-gray-200 rounded-lg p-4 mb-4 hover:shadow-md transition-shadow">
                    <h5 class="text-xl font-bold text-gray-800 mb-2">${titleWithoutNumber}</h5>
                    <p class="text-gray-600 text-base mb-4">by <strong class="text-gray-800">${cleanArtist}</strong></p>
                    
                    <div class="grid grid-cols-3 gap-2 mb-4">
                        <div class="p-2 rounded text-center font-semibold text-sm" style="background-color: #f0f8e6; color: #76B900;">🎸 ${song.genre || 'Various'}</div>
                        <div class="bg-purple-50 text-purple-700 p-2 rounded text-center font-semibold text-sm">✨ ${song.mood || 'Upbeat'}</div>
                        <div class="bg-green-50 text-green-700 p-2 rounded text-center font-semibold text-sm">📱 ${song.best_for || 'Social Media'}</div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3">
                        <a href="${spotifyUrl}" target="_blank" 
                           class="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded text-center transition-all shadow-md hover:shadow-lg">
                            🎵 Listen on Spotify
                        </a>
                        <a href="${youtubeUrl}" target="_blank" 
                           class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-4 rounded text-center transition-all shadow-md hover:shadow-lg">
                            ▶️ Watch on YouTube
                        </a>
                    </div>
                </div>
            `;
        });
        
        // Summary
        const uniqueGenres = new Set(musicRec.songs.map(s => s.genre));
        const uniqueMoods = new Set(musicRec.songs.map(s => s.mood));
        
        html += `
            <div class="mt-6 grid grid-cols-3 gap-4">
                <div class="p-4 rounded-lg text-center" style="background-color: #f0f8e6;">
                    <div class="text-2xl font-bold" style="color: #76B900;">${musicRec.songs.length}</div>
                    <div class="text-sm text-gray-600">🎵 Total Songs</div>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-purple-600">${uniqueGenres.size}</div>
                    <div class="text-sm text-gray-600">🎸 Genres</div>
                </div>
                <div class="bg-green-50 p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-green-600">${uniqueMoods.size}</div>
                    <div class="text-sm text-gray-600">✨ Moods</div>
                </div>
            </div>
        `;
    } else {
        html += '<p class="text-gray-600">No songs found.</p>';
    }
    
    document.getElementById('music-content').innerHTML = html;
}

// Display agent log
function displayCityHistory(cityHistory) {
    const historyContent = document.getElementById('history-content');
    if (!historyContent) {
        console.warn('History content element not found');
        return;
    }
    
    if (!cityHistory || !cityHistory.history) {
        historyContent.innerHTML = `
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-2xl font-bold mb-4 text-gray-800">📚 City History</h3>
                <p class="text-gray-600">No history information available for this destination.</p>
            </div>
        `;
        return;
    }
    
    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    const destination = escapeHtml(cityHistory.destination || 'Unknown');
    const history = escapeHtml(cityHistory.history || '');
    const source = cityHistory.source || 'unknown';
    
    const sourceBadge = source === 'gemini_api' 
        ? '<span class="inline-block bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded ml-2">✨ AI Generated</span>'
        : '<span class="inline-block bg-gray-100 text-gray-800 text-xs font-semibold px-2 py-1 rounded ml-2">📖 Default</span>';
    
    historyContent.innerHTML = `
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-2xl font-bold mb-4 text-gray-800">
                📚 History of ${destination}
                ${sourceBadge}
            </h3>
            <div class="prose max-w-none">
                <p class="text-gray-700 text-lg leading-relaxed mb-4 whitespace-pre-wrap">${history}</p>
            </div>
            ${cityHistory.length > 0 ? `<p class="text-sm text-gray-500 mt-4">${cityHistory.length} characters</p>` : ''}
        </div>
    `;
}


function displayAgentLog(agentState) {
    if (!agentState || !agentState.log || agentState.log.length === 0) {
        return;
    }
    
    let html = '';
    agentState.log.forEach((result, index) => {
        html += `
            <div class="border-l-4 border-green-500 bg-white p-4 mb-4 rounded">
                <div class="font-semibold text-gray-800 mb-2">Step ${index + 1}: ${result.tool}</div>
                <div class="text-sm text-gray-600 mb-2">
                    <strong>Input:</strong> <pre class="bg-gray-50 p-2 rounded mt-1">${JSON.stringify(result.input, null, 2)}</pre>
                </div>
                <div class="text-sm text-gray-600 mb-2">
                    <strong>Cost:</strong> $${result.cost_estimate.toFixed(2)}
                </div>
                ${result.notes ? `<div class="text-sm text-gray-600 mb-2"><strong>Notes:</strong> ${result.notes}</div>` : ''}
                ${result.thinking ? `
                    <div class="bg-yellow-50 border-l-4 border-yellow-500 p-3 mt-2 rounded">
                        <strong>🤔 Agent Thinking:</strong>
                        <pre class="text-sm mt-1 whitespace-pre-wrap">${result.thinking}</pre>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    document.getElementById('log-content').innerHTML = html;
    document.getElementById('agent-log').classList.remove('hidden');
}

// Switch tabs
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active', 'border-b-2');
        button.classList.add('text-gray-500');
        button.style.color = '';
        button.style.borderColor = '';
    });
    
    // Show selected tab content
    const tabContent = document.getElementById(`tab-${tabName}`);
    if (tabContent) {
        tabContent.classList.remove('hidden');
    }
    
    // Add active class to selected button
    const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeButton) {
        activeButton.classList.add('active', 'border-b-2');
        activeButton.classList.remove('text-gray-500');
        activeButton.style.color = '#76B900';
        activeButton.style.borderColor = '#76B900';
    }
    
    // Re-render map if switching to map tab
    if (tabName === 'map' && currentItinerary) {
        // Small delay to ensure tab is visible before initializing map
        setTimeout(() => {
            displayMap(currentItinerary);
        }, 50);
    }
}

// Download JSON
function downloadJSON() {
    if (!currentItinerary || !currentUserRequest) return;
    
    const data = {
        user_request: currentUserRequest,
        itinerary: currentItinerary
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `itinerary_${currentUserRequest.destination.replace(' ', '_')}_${currentUserRequest.start_date}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Download calendar
function downloadCalendar() {
    if (!currentItinerary || !currentUserRequest) return;
    
    // This would require calling the backend API for calendar generation
    showStatus('Calendar download not yet implemented', 'info');
}

// Show status message
function showStatus(message, type = 'info') {
    const banner = document.getElementById('status-banner');
    const messageEl = document.getElementById('status-message');
    
    banner.className = `mb-6 p-4 rounded-lg ${type === 'error' ? 'bg-red-100 text-red-800' : type === 'success' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`;
    messageEl.textContent = message;
    banner.classList.remove('hidden');
    
    setTimeout(() => {
        banner.classList.add('hidden');
    }, 5000);
}

