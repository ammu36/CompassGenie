import pytest
from unittest.mock import patch
from app.services.google_maps import _geocode_address, decode_polyline


# --- 1. Testing Logic without APIs ---
def test_decode_polyline():
    """Test the polyline decoder with a known Google encoded string."""
    encoded = "_p~iF~ps|U_ulLnnqC"
    expected = [
        {"lat": 38.5, "lng": -120.2},
        {"lat": 40.7, "lng": -120.95}
    ]

    result = decode_polyline(encoded)
    assert result == pytest.approx(expected)


# --- 2. Testing API Logic with Mocks ---
@patch('app.services.google_maps.requests.get')
def test_geocode_address_success(mock_get):
    """Test geocoding logic by mocking a successful Google API response."""
    # Mock the internal JSON response from Google
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "OK",
        "results": [{
            "geometry": {"location": {"lat": 10.0, "lng": 20.0}}
        }]
    }

    result = _geocode_address("Some Famous Landmark")

    assert result == {"lat": 10.0, "lng": 20.0}
    mock_get.assert_called_once()  # Ensure the API was actually "hit"


@patch('app.services.google_maps.requests.get')
def test_geocode_address_failure(mock_get):
    """Test how the system handles a 'ZERO_RESULTS' response."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "ZERO_RESULTS", "results": []}

    result = _geocode_address("NonExistentPlace12345")
    assert result is None