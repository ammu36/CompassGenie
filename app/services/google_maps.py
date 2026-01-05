import json
import requests
from typing import Dict, Any, List
from langchain_core.tools import tool

from ..core.config import settings


def _fetch_maps_data(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Robust helper for Google Maps API requests."""
    if settings.MAPS_MOCK_ENABLED:
        # Mock Response for testing
        print("DEBUG: Using Mock Data")
        return {"results": [{"name": "Mock Place in Requested City", "rating": 4.5,
                             "geometry": {"location": {"lat": 28.4595, "lng": 77.0266}}}]}

    try:
        params['key'] = settings.MAPS_API_KEY
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK":
            return data
        elif data.get("status") == "ZERO_RESULTS":
            return {"results": []}
        else:
            print(f"Maps Error: {data.get('status')} - {data.get('error_message', '')}")
            return {"error_message": f"Maps Error: {data.get('status')} - {data.get('error_message', '')}"}
    except Exception as e:
        print(str(e))
        return {"error_message": str(e)}


def _geocode_address(address: str) -> Dict[str, float] | None:
    """Geocodes a text address to latitude and longitude."""
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    if settings.MAPS_MOCK_ENABLED:
        print("DEBUG: Using Mock Geocode")
        return {"lat": 28.4526, "lng": 77.0863}  # Example coordinates

    params = {'address': address, 'key': settings.MAPS_API_KEY}

    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return {"lat": location["lat"], "lng": location["lng"]}
        return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding Error: {e}")
        return None


def decode_polyline(polyline_str: str) -> List[Dict[str, float]]:
    """Decodes a Google Maps encoded polyline string."""
    # The original decode_polyline logic remains here
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    while index < len(polyline_str):
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if byte < 0x20:
                    break
            if result & 1:
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']
        coordinates.append({"lat": lat / 100000.0, "lng": lng / 100000.0})

    return coordinates

@tool
def maps_api_search(search_term: str, latitude: float, longitude: float, search_type: str = "nearby",
                    origin_override: str = None) -> str:
    """
    Searches Google Maps for nearby places or calculates a driving route.
    search_type: 'nearby' (finds places), 'route' (calculates directions).
    """
    # Placeholder for LLM import from agent_service to avoid circular dependency
    from .agent_service import llm

    base_url = "https://maps.googleapis.com/maps/api/"
    results = {
        "response_text": "I was unable to find results.",
        "map_data": {"points": [], "routes": []}
    }

    # 1. SEARCH LOGIC (Text Search)
    if search_type == "nearby" and search_term:
        url = base_url + "place/textsearch/json"
        params = {
            "query": search_term,
            "location": f"{latitude},{longitude}",
            "radius": 10000
        }
        api_response = _fetch_maps_data(url, params)

        if "error_message" in api_response:
            return json.dumps({"response_text": api_response['error_message'], "map_data": {}})

        if api_response.get("results"):
            points = []
            response_lines = [f"Here are the results for **'{search_term}'**:"]

            for i, result in enumerate(api_response["results"][:5]):
                lat = result["geometry"]["location"]["lat"]
                lng = result["geometry"]["location"]["lng"]
                name = result.get("name", f"Result {i + 1}")
                rating = result.get("rating", "N/A")
                address = result.get("formatted_address", "")

                points.append({"name": name, "latitude": lat, "longitude": lng})

                response_lines.append(f"* **{name}** ({rating}⭐)\n  _{address}_")

            results["response_text"] = "\n".join(response_lines)
            results["map_data"]["points"] = points
        else:
            results["response_text"] = f"I couldn't find any places matching '{search_term}'."

    # 2. ROUTE LOGIC
    if search_type == "route" and search_term:
        origin_address = f"{latitude},{longitude}"
        origin_name = "Current Location"

        if origin_override:
            new_origin_coords = _geocode_address(origin_override)
            if new_origin_coords:
                origin_address = f"{new_origin_coords['lat']},{new_origin_coords['lng']}"
                origin_name = origin_override
            else:
                results["response_text"] = f"Warning: Could not locate '{origin_override}'. Using GPS location."

        url = base_url + "directions/json"
        params = {"origin": origin_address, "destination": search_term, "mode": "driving"}
        api_response = _fetch_maps_data(url, params)

        if "error_message" in api_response:
            return json.dumps({"response_text": api_response['error_message'], "map_data": {}})

        if api_response.get("routes"):
            route = api_response["routes"][0]
            leg = route["legs"][0]
            distance = leg["distance"]["text"]
            duration = leg["duration"]["text"]
            route_path = decode_polyline(route["overview_polyline"]["points"])

            # Brief AI advice
            try:
                advice_prompt = f"Give 1 short traffic tip for driving from {origin_name} to {search_term}."
                ai_advice = llm.invoke(advice_prompt).content
            except:
                ai_advice = "* Drive safely!"

            results["response_text"] = (
                f"### Route from {origin_name} to {search_term}\n"
                f"* 🚗 **Distance:** {distance}\n"
                f"* ⏱️ **Time:** {duration}\n\n"
                f"**Note:**\n{ai_advice}"
            )
            results["map_data"]["routes"] = [{"path": route_path}]

            if origin_name != "Current Location":
                results["map_data"]["points"].append({
                    "name": origin_name,
                    "latitude": float(origin_address.split(',')[0]),
                    "longitude": float(origin_address.split(',')[1]),
                    "color": "blue"
                })

            results["map_data"]["points"].append({
                "name": search_term,
                "latitude": route_path[-1]['lat'],
                "longitude": route_path[-1]['lng']
            })
        else:
            results["response_text"] = f"I couldn't find a route from {origin_name} to '{search_term}'."

    return json.dumps(results)