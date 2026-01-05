import requests
from langchain_core.tools import tool
from ..core.config import settings


@tool
def get_aqi(location_name: str = None, lat: float = None, lng: float = None) -> str:
    """
    Fetches the Air Quality Index (0-500 scale) and health recommendations.
    Uses 'location_name' or 'lat'/'lng' coordinates.
    """
    api_key = settings.MAPS_API_KEY

    # --- Geocoding Logic ---
    if location_name:
        geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={api_key}"
        geo_res = requests.get(geo_url).json()
        if not geo_res.get("results"):
            return f"Could not find coordinates for {location_name}."
        loc = geo_res["results"][0]["geometry"]["location"]
        target_lat, target_lng = loc["lat"], loc["lng"]
        display_name = location_name
    else:
        target_lat, target_lng = lat, lng
        display_name = "your current location"

    # --- AQI & Recommendations Request ---
    aqi_url = f"https://airquality.googleapis.com/v1/currentConditions:lookup?key={api_key}"
    payload = {
        "location": {"latitude": target_lat, "longitude": target_lng},
        "extraComputations": [
            "LOCAL_AQI",
            "HEALTH_RECOMMENDATIONS",
            "DOMINANT_POLLUTANT_CONCENTRATION"
        ]
    }

    try:
        response = requests.post(aqi_url, json=payload)
        data = response.json()

        # 1. Get 0-500 scale (Local AQI)
        indexes = data.get("indexes", [])
        local_aqi = next((idx for idx in indexes if idx["code"] != "uaqi"), indexes[0])

        # 2. Get Health Recommendations
        recs = data.get("healthRecommendations", {})

        # Format the output with clear sections
        output = [
            f"## Air Quality for {display_name}",
            f"**AQI:** {local_aqi['aqi']} ({local_aqi['category']})",
            f"**Dominant Pollutant:** {data.get('dominantPollutant', 'N/A')}",
            "\n### 💡 Health Recommendations",
            f"* **General Public:** {recs.get('generalPopulation', 'No specific advice.')}",
            f"* **Sensitive Groups:** {recs.get('lungDiseasePopulation', recs.get('children', 'Take extra precautions if you have respiratory issues.'))}"
        ]

        # Add a specific alert for high pollution
        if local_aqi['aqi'] > 150:
            output.insert(1, "⚠️ **WARNING: Unhealthy air levels detected.**")

        return "\n".join(output)

    except Exception as e:
        return f"Error retrieving data: {str(e)}"