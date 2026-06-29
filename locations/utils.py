import urllib.request
import urllib.parse
import json
import logging
import math

logger = logging.getLogger(__name__)

def fetch_coordinates_nominatim(city, area, pin_code):
    """
    Fetches latitude and longitude from OpenStreetMap Nominatim API.
    Returns (lat, lon) as floats or (None, None) if not found/error.
    """
    headers = {
        'User-Agent': 'GroceriesDeliveryApp/1.0 (contact: support@groceryapp.com)'
    }
    
    # Try query with India suffix first
    query = f"{area}, {city}, {pin_code}, India"
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f"Nominatim resolved '{query}' to ({lat}, {lon})")
                return lat, lon
    except Exception as e:
        logger.error(f"Error fetching coordinates from Nominatim for '{query}': {e}")
        
    # Fallback to broader query (city, pin_code, India)
    query_fallback = f"{city}, {pin_code}, India"
    url_fallback = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_fallback)}&format=json&limit=1"
    try:
        req = urllib.request.Request(url_fallback, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f"Nominatim fallback resolved '{query_fallback}' to ({lat}, {lon})")
                return lat, lon
    except Exception as ex:
        logger.error(f"Error fetching fallback coordinates for '{query_fallback}': {ex}")
        
    # Second fallback: without country suffix just in case (city, pin_code)
    query_fallback_2 = f"{city}, {pin_code}"
    url_fallback_2 = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_fallback_2)}&format=json&limit=1"
    try:
        req = urllib.request.Request(url_fallback_2, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f"Nominatim fallback 2 resolved '{query_fallback_2}' to ({lat}, {lon})")
                return lat, lon
    except Exception as ex2:
        logger.error(f"Error fetching fallback 2 coordinates for '{query_fallback_2}': {ex2}")
        
    return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula.
    Returns distance in kilometers.
    """
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    r = 6371.0  # Earth's radius in kilometers
    return r * c
