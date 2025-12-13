// --- CONFIGURATION ---
const BACKEND_URL = "http://127.0.0.1:8000/chat"; // Backend URL is now central here

// --- GLOBAL STATE ---
let map;
let userLocation = null;
let markers = [];
let routes = [];

// --- UTILITIES ---
function showMessage(message, type = 'error') {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.className = type === 'error' ? 'text-red-500 text-sm' : 'text-green-500 text-sm';
    errorDiv.style.display = 'block';
    setTimeout(() => { errorDiv.style.display = 'none'; }, 5000);
}

// --- 1. GEOLOCATION ---
function getUserLocation() {
    const statusElement = document.getElementById('lat-lng');
    const sendButton = document.getElementById('send-btn');
    statusElement.textContent = 'Acquiring...';

    const DEFAULT_LOCATION = { lat: 34.0522, lng: -118.2437 }; // LA Default

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
                statusElement.textContent = `Lat: ${userLocation.lat.toFixed(4)}, Lng: ${userLocation.lng.toFixed(4)}`;
                sendButton.disabled = false;
                if (map) {
                    map.setCenter(userLocation);
                    map.setZoom(14);
                    addMarker(userLocation, "Current Location", 'blue');
                }
            },
            (error) => {
                console.error("Geolocation failed:", error);
                userLocation = DEFAULT_LOCATION;
                statusElement.textContent = `Fallback: Lat: ${userLocation.lat.toFixed(4)}, Lng: ${userLocation.lng.toFixed(4)}`;
                showMessage("Could not get location. Using default.", 'error');
                sendButton.disabled = false;
                if (map) {
                    map.setCenter(userLocation);
                    addMarker(userLocation, "Fallback Location", 'purple');
                }
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        userLocation = DEFAULT_LOCATION;
        statusElement.textContent = 'Geo not supported';
        sendButton.disabled = false;
    }
}

// --- 2. GOOGLE MAPS CORE FUNCTIONS ---

// NOTE: This function must be globally accessible for the Google Maps API to call it
window.initMap = function() {
    const mapContainer = document.getElementById('map');
    document.getElementById('map-loading').style.display = 'none';

    map = new google.maps.Map(mapContainer, {
        center: { lat: 34.0522, lng: -118.2437 },
        zoom: 10,
        streetViewControl: false,
        mapTypeControl: false
    });

    getUserLocation();
}

function clearMap() {
    markers.forEach(marker => marker.setMap(null));
    markers = [];
    routes.forEach(route => route.setMap(null));
    routes = [];
}

function addMarker(location, title, color = 'red') {
    const marker = new google.maps.Marker({
        position: location,
        map: map,
        title: title,
        // The color logic needs to use the proper marker URL structure
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
    const bounds = new google.maps.LatLngBounds();
    let hasContent = false;

    // Markers
    if (mapData.points && mapData.points.length > 0) {
        hasContent = true;

        // Add current location marker only if route planning didn't add an 'origin_override'
        const hasCustomOrigin = mapData.points.some(p => p.color === 'blue');

        if (userLocation && !hasCustomOrigin) {
            const uM = addMarker(userLocation, "You", 'blue');
            bounds.extend(uM.getPosition());
        }

        mapData.points.forEach(point => {
            // Use the point's color property if available (for custom origins)
            const markerColor = point.color || 'red';
            const m = addMarker({ lat: point.latitude, lng: point.longitude }, point.name, markerColor);
            bounds.extend(m.getPosition());
        });
    }

    // Routes
    if (mapData.routes && mapData.routes.length > 0) {
        hasContent = true;
        // The route logic ensures bounds cover the entire route
        mapData.routes.forEach(route => {
            if (route.path && route.path.length > 0) {
                drawRoute(route.path);
                route.path.forEach(coord => bounds.extend(coord));
            }
        });
    }

    if (hasContent) {
        map.fitBounds(bounds);
        const listener = google.maps.event.addListener(map, "idle", () => {
            // Adjust zoom to prevent being too close after fitting bounds
            if (map.getZoom() > 15) map.setZoom(15);
            google.maps.event.removeListener(listener);
        });
    }
}


// --- 3. BACKEND COMMUNICATION ---

// NOTE: This function is globally accessible via the onclick="handleChat()" attribute
window.handleChat = async function() {
    const inputElement = document.getElementById('user-input');
    const query = inputElement.value.trim();
    if (!query) return;

    if (!userLocation) {
        showMessage("Location not ready yet.", 'error');
        return;
    }

    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-btn');
    const loadingIndicator = document.getElementById('loading-indicator');

    // 1. Render User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'flex justify-end';
    userMsgDiv.innerHTML = `<div class="bg-green-100 p-3 max-w-[85%] rounded-xl shadow-md">
                                <p class="font-medium text-green-900">${query}</p>
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
             throw new Error(errorData.detail || "API Error");
        }

        const data = await response.json();

        // 2. Render AI Message (With Markdown Parsing)
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.className = 'flex justify-start';

        // Use marked for MD parsing
        const formattedHtml = marked.parse(data.response_text);

        aiMsgDiv.innerHTML = `<div class="bg-white p-4 max-w-[90%] rounded-xl shadow-md text-sm text-gray-800 leading-relaxed chat-content">
                                    ${formattedHtml}
                                </div>`;

        chatBox.appendChild(aiMsgDiv);

        // 3. Update Map
        if (data.map_data) {
            updateMap(data.map_data);
        }

    } catch (error) {
        console.error(error);
        showMessage(`Failed to connect to CompassGenie: ${error.message}`, 'error');
    } finally {
        sendButton.disabled = false;
        loadingIndicator.style.display = 'none';
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}