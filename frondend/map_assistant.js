// --- CONFIGURATION ---
const BACKEND_URL = "http://localhost:8000/chat";

// --- GLOBAL STATE ---
let map;
let userLocation = null;
let markers = [];
let routes = [];

// --- UTILITIES ---
function showMessage(message, type = 'error') {
    const errorDiv = document.getElementById('error-message');
    if (!errorDiv) return;
    errorDiv.textContent = message;
    errorDiv.className = type === 'error' ? 'text-red-500 text-sm p-2' : 'text-blue-500 text-sm p-2';
    errorDiv.style.display = 'block';
    setTimeout(() => { errorDiv.style.display = 'none'; }, 8000);
}

// --- 1. GEOLOCATION (Improved with Fallbacks & Better Timeout) ---
function getUserLocation(isRetry = false) {
    const statusElement = document.getElementById('lat-lng');
    const sendButton = document.getElementById('send-btn');
    statusElement.textContent = isRetry ? 'Retrying...' : 'Acquiring...';

    // Default to South Delhi for your project context
    const DEFAULT_LOCATION = { lat: 28.5272, lng: 77.2159 };

    const geoOptions = {
        enableHighAccuracy: !isRetry, // Try high accuracy first, then low on retry
        timeout: isRetry ? 20000 : 10000,
        maximumAge: 60000 // Use a cached position if available within 1 minute
    };

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                statusElement.textContent = `Lat: ${userLocation.lat.toFixed(4)}, Lng: ${userLocation.lng.toFixed(4)}`;
                sendButton.disabled = false;
                if (map) {
                    map.setCenter(userLocation);
                    map.setZoom(14);
                    addMarker(userLocation, "You", 'blue');
                }
            },
            (error) => {
                console.warn("Geolocation attempt failed:", error.message);

                if (!isRetry && error.code === error.TIMEOUT) {
                    // Try one more time with lower accuracy requirements
                    getUserLocation(true);
                } else {
                    // Final Fallback
                    userLocation = DEFAULT_LOCATION;
                    statusElement.textContent = `Delhi (Default): ${userLocation.lat}, ${userLocation.lng}`;
                    sendButton.disabled = false;

                    if (error.code === error.PERMISSION_DENIED) {
                        showMessage("Location blocked by system. Using default (Delhi).", 'warning');
                    } else {
                        showMessage("GPS Timeout. Using default (Delhi).", 'error');
                    }

                    if (map) {
                        map.setCenter(userLocation);
                        addMarker(userLocation, "Default Location", 'purple');
                    }
                }
            },
            geoOptions
        );
    } else {
        userLocation = DEFAULT_LOCATION;
        statusElement.textContent = 'Geo not supported';
        sendButton.disabled = false;
    }
}

// --- 2. GOOGLE MAPS CORE FUNCTIONS ---
window.initMap = function() {
    const mapContainer = document.getElementById('map');
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'none';

    map = new google.maps.Map(mapContainer, {
        center: { lat: 28.5272, lng: 77.2159 }, // South Delhi
        zoom: 12,
        streetViewControl: false,
        mapTypeControl: false,
        styles: [ { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] } ]
    });

    getUserLocation();
};

function clearMap() {
    markers.forEach(m => m.setMap(null));
    markers = [];
    routes.forEach(r => r.setMap(null));
    routes = [];
}

function addMarker(location, title, color = 'red') {
    const marker = new google.maps.Marker({
        position: location,
        map: map,
        title: title,
        icon: { url: `http://maps.google.com/mapfiles/ms/icons/${color}-dot.png` }
    });
    markers.push(marker);
    return marker;
}

function drawRoute(points, color = '#7C3AED') {
    const path = new google.maps.Polyline({
        path: points,
        geodesic: true,
        strokeColor: color,
        strokeOpacity: 0.8,
        strokeWeight: 5
    });
    path.setMap(map);
    routes.push(path);
}

function updateMap(mapData) {
    clearMap();
    if (!mapData) return;

    const bounds = new google.maps.LatLngBounds();
    let hasContent = false;

    // Add Points/Markers
    if (mapData.points && mapData.points.length > 0) {
        hasContent = true;
        mapData.points.forEach(point => {
            const m = addMarker({ lat: point.latitude, lng: point.longitude }, point.name, point.color || 'red');
            bounds.extend(m.getPosition());
        });
    }

    // Draw Routes
    if (mapData.routes && mapData.routes.length > 0) {
        hasContent = true;
        mapData.routes.forEach(route => {
            if (route.path && route.path.length > 0) {
                drawRoute(route.path, route.color || '#7C3AED');
                route.path.forEach(coord => bounds.extend(coord));
            }
        });
    }

    if (hasContent) {
        map.fitBounds(bounds);
        // Prevent overly aggressive zooming
        const listener = google.maps.event.addListener(map, "idle", () => {
            if (map.getZoom() > 16) map.setZoom(16);
            google.maps.event.removeListener(listener);
        });
    }
}

// --- 3. BACKEND COMMUNICATION ---
window.handleChat = async function() {
    const inputElement = document.getElementById('user-input');
    const query = inputElement.value.trim();
    if (!query) return;

    if (!userLocation) {
        showMessage("Acquiring location... please wait a moment.", 'warning');
        return;
    }

    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-btn');
    const loadingIndicator = document.getElementById('loading-indicator');

    // Render User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'flex justify-end mb-4';
    userMsgDiv.innerHTML = `<div class="bg-indigo-600 text-white p-3 max-w-[85%] rounded-2xl shadow-sm">
                                <p class="text-sm">${query}</p>
                            </div>`;
    chatBox.appendChild(userMsgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    inputElement.value = '';
    sendButton.disabled = true;
    loadingIndicator.style.display = 'block';

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, location: userLocation })
        });

        if (!response.ok) {
             const errorData = await response.json();
             throw new Error(errorData.detail || "Engine Error");
        }

        const data = await response.json();

        // Render AI Message
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.className = 'flex justify-start mb-4';
        const formattedHtml = typeof marked !== 'undefined' ? marked.parse(data.response_text) : data.response_text;

        aiMsgDiv.innerHTML = `<div class="bg-gray-100 p-4 max-w-[90%] rounded-2xl shadow-inner text-sm text-gray-800 leading-relaxed">
                                    ${formattedHtml}
                                </div>`;

        chatBox.appendChild(aiMsgDiv);

        if (data.map_data) {
            updateMap(data.map_data);
        }

    } catch (error) {
        console.error("Chat Error:", error);
        showMessage(`CompassGenie Error: ${error.message}`, 'error');
    } finally {
        sendButton.disabled = false;
        loadingIndicator.style.display = 'none';
        chatBox.scrollTop = chatBox.scrollHeight;
    }
};