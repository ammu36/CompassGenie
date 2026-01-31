// --- CONFIGURATION ---
const BACKEND_URL = "http://localhost:8000/chat";

// --- GLOBAL STATE ---
let map;
let userLocation = null;
let markers = [];
let routes = [];
let selectedImageBase64 = null; // Stores the image to send

// --- 1. IMAGE HANDLING ---
/**
 * Triggered when a user selects a file via the camera/upload button
 */
function previewImage(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            // Get the full Data URL (data:image/jpeg;base64,...)
            const fullDataUrl = e.target.result;

            // Store just the Base64 portion for the API
            selectedImageBase64 = fullDataUrl.split(',')[1];

            // Update the UI preview
            const previewImg = document.getElementById('image-preview');
            const previewContainer = document.getElementById('image-preview-container');

            previewImg.src = fullDataUrl;
            previewContainer.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

/**
 * Resets the image selection
 */
function clearImage() {
    selectedImageBase64 = null;
    document.getElementById('image-input').value = "";
    document.getElementById('image-preview-container').classList.add('hidden');
}

// --- 2. GEOLOCATION (With Fallbacks) ---
function getUserLocation(isRetry = false) {
    const statusElement = document.getElementById('lat-lng');
    const sendButton = document.getElementById('send-btn');
    const DEFAULT_LOCATION = { lat: 28.5272, lng: 77.2159 }; // South Delhi

    if (!navigator.geolocation) {
        setFinalLocation(DEFAULT_LOCATION, "Geo not supported");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = { lat: position.coords.latitude, lng: position.coords.longitude };
            setFinalLocation(userLocation, `Lat: ${userLocation.lat.toFixed(4)}, Lng: ${userLocation.lng.toFixed(4)}`);
            addMarker(userLocation, "You", 'blue');
        },
        (error) => {
            if (!isRetry && error.code === error.TIMEOUT) {
                getUserLocation(true);
            } else {
                userLocation = DEFAULT_LOCATION;
                setFinalLocation(userLocation, "Delhi (Default)");
                addMarker(userLocation, "Default", 'purple');
            }
        },
        { enableHighAccuracy: !isRetry, timeout: 10000 }
    );

    function setFinalLocation(loc, text) {
        statusElement.textContent = text;
        sendButton.disabled = false;
        if (map) map.setCenter(loc);
    }
}

// --- 3. GOOGLE MAPS CORE ---
window.initMap = function() {
    const mapContainer = document.getElementById('map');
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'none';

    map = new google.maps.Map(mapContainer, {
        center: { lat: 28.5272, lng: 77.2159 },
        zoom: 13,
        styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
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

function updateMap(mapData) {
    clearMap();
    if (!mapData) return;
    const bounds = new google.maps.LatLngBounds();
    let hasContent = false;

    if (mapData.points) {
        mapData.points.forEach(p => {
            const m = addMarker({ lat: p.latitude, lng: p.longitude }, p.name, p.color);
            bounds.extend(m.getPosition());
            hasContent = true;
        });
    }

    if (hasContent) map.fitBounds(bounds);
}

// --- 4. CHAT & BACKEND SYNC ---
window.handleChat = async function() {
    const inputElement = document.getElementById('user-input');
    const query = inputElement.value.trim();

    // Validate: Need either text OR an image to proceed
    if (!query && !selectedImageBase64) return;

    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-btn');
    const loadingIndicator = document.getElementById('loading-indicator');

    // 1. UI: Append User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'flex justify-end mb-4';

    // If an image was sent, show a small thumbnail in the chat bubble
    const imgHtml = selectedImageBase64 ? `<img src="data:image/jpeg;base64,${selectedImageBase64}" class="max-w-xs rounded-lg mb-2 border-2 border-white shadow-sm">` : '';

    userMsgDiv.innerHTML = `
        <div class="bg-indigo-600 text-white p-3 max-w-[85%] rounded-2xl shadow-md">
            ${imgHtml}
            <p class="text-sm">${query || "<i>Sent an image</i>"}</p>
        </div>`;
    chatBox.appendChild(userMsgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. Prepare Request
    inputElement.value = '';
    sendButton.disabled = true;
    loadingIndicator.classList.remove('hidden');

    // Local copy of image to send (then clear the UI immediately)
    const imageToSend = selectedImageBase64;
    clearImage();

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                location: userLocation,
                image: imageToSend // This is the key field for multimodal
            })
        });

        if (!response.ok) throw new Error("Engine Error");

        const data = await response.json();

        // 3. UI: Append AI Response
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.className = 'flex justify-start mb-4';
        const formattedHtml = typeof marked !== 'undefined' ? marked.parse(data.response_text) : data.response_text;

        aiMsgDiv.innerHTML = `
            <div class="bg-gray-100 p-4 max-w-[90%] rounded-2xl shadow-inner text-sm text-gray-800 leading-relaxed">
                ${formattedHtml}
            </div>`;
        chatBox.appendChild(aiMsgDiv);

        if (data.map_data) updateMap(data.map_data);

    } catch (error) {
        console.error("Chat Error:", error);
        const errDiv = document.getElementById('error-message');
        errDiv.textContent = "Error: " + error.message;
        errDiv.classList.remove('hidden');
    } finally {
        sendButton.disabled = false;
        loadingIndicator.classList.add('hidden');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
};

function showMessage(msg, type) {
    const errDiv = document.getElementById('error-message');
    errDiv.textContent = msg;
    errDiv.classList.remove('hidden');
    setTimeout(() => errDiv.classList.add('hidden'), 5000);
}