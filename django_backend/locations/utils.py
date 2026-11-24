import math
import os
import requests
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def is_valid_api_key(key):
    return bool(key and not key.startswith("your_"))

def deg2rad(deg):
    return deg * (math.pi / 180.0)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate the distance between two lat/lng points.
    @returns distance in kilometers
    """
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return 0.0

    R = 6371.0 # Earth radius in km
    d_lat = deg2rad(lat2 - lat1)
    d_lon = deg2rad(lon2 - lon1)

    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(deg2rad(lat1))
        * math.cos(deg2rad(lat2))
        * (math.sin(d_lon / 2.0) ** 2)
    )

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

# Fallback known coordinates for major Indian districts/states
KNOWN_LOCATIONS = {
    "agra": (27.1767, 78.0081),
    "aligarh": (27.8974, 78.0880),
    "allahabad": (25.4358, 81.8463),
    "prayagraj": (25.4358, 81.8463),
    "bareilly": (28.3670, 79.4304),
    "gorakhpur": (26.7606, 83.3732),
    "kanpur": (26.4499, 80.3319),
    "lucknow": (26.8467, 80.9462),
    "meerut": (28.9845, 77.7064),
    "mirzapur": (25.1337, 82.5644),
    "moradabad": (28.8386, 78.7733),
    "varanasi": (25.3176, 82.9739),
    "mohali": (30.7046, 76.7179),
    "ludhiana": (30.9010, 75.8573),
    "amritsar": (31.6340, 74.8723),
    "jalandhar": (31.3260, 75.5762),
    "patiala": (30.3398, 76.3869),
    "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126),
    "gwalior": (26.2183, 78.1828),
    "jabalpur": (23.1815, 79.9864),
    "ujjain": (23.1765, 75.7885),
    "jaipur": (26.9124, 75.7873),
    "jodhpur": (26.2389, 73.0243),
    "kota": (25.2138, 75.8648),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "pune": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "nashik": (19.9975, 73.7898),
    "ahmedabad": (23.0225, 72.5714),
    "surat": (21.1702, 72.8311),
    "vadodara": (22.3072, 73.1812),
    "rajkot": (22.3039, 70.8022),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "patna": (25.5941, 85.1376),
    "ranchi": (23.3441, 85.3096),
    "raipur": (21.2514, 81.6296),
    "bhubaneswar": (20.2961, 85.8245),
}

def get_coordinates(village="", district="", state=""):
    """
    Geocode using OpenCage API, falling back to local lookup and Nominatim.
    """
    # 1. Check known local coordinates first
    for name in [str(village).lower(), str(district).lower(), str(state).lower()]:
        clean = name.replace("district", "").strip()
        if clean in KNOWN_LOCATIONS:
            lat, lon = KNOWN_LOCATIONS[clean]
            return {"latitude": lat, "longitude": lon}

    api_key = os.getenv("OPENCAGE_API_KEY", "").strip()

    # 2. Try OpenCage if real key is configured
    if is_valid_api_key(api_key):
        try:
            query = f"{village}, {district}, {state}, India".strip(", ")
            url = f"https://api.opencagedata.com/geocode/v1/json?q={requests.utils.quote(query)}&key={api_key}"
            res = requests.get(url, timeout=3, verify=False)
            if res.status_code == 200:
                data = res.json()
                if data.get("results"):
                    geom = data["results"][0]["geometry"]
                    return {"latitude": geom["lat"], "longitude": geom["lng"]}
        except Exception as e:
            logger.warning(f"OpenCage geocoding error: {e}")

    # 3. Try OpenStreetMap Nominatim
    try:
        query_parts = [p for p in [village, district, state, "India"] if p]
        query = ", ".join(query_parts)
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent": "AgroAISystem/1.0"}, timeout=2)
        if res.status_code == 200:
            results = res.json()
            if results:
                return {
                    "latitude": float(results[0]["lat"]),
                    "longitude": float(results[0]["lon"]),
                }
    except Exception as e:
        logger.warning(f"Nominatim geocoding error: {e}")

    # Default fallback near central India
    return {"latitude": 25.1337, "longitude": 82.5644}
