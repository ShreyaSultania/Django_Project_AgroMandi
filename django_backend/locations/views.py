import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework import status
from core.utils import success_response, error_response
from .utils import KNOWN_LOCATIONS, haversine_distance, is_valid_api_key

logger = logging.getLogger(__name__)

class ReverseGeocodeView(APIView):
    """
    GET /api/location/reverse?lat=...&lon=...
    Replaces Express reverseGeocode controller.
    """
    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            return error_response(
                message="Missing parameters",
                error="Latitude and Longitude are required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        api_key = os.getenv("OPENCAGE_API_KEY", "").strip()

        # 1. Try OpenCage if real key is configured
        if is_valid_api_key(api_key):
            try:
                url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}"
                res = requests.get(url, timeout=3, verify=False)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        components = results[0].get("components", {})
                        village = (
                            components.get("village")
                            or components.get("town")
                            or components.get("city")
                            or components.get("suburb")
                            or components.get("neighbourhood")
                            or ""
                        )
                        district = components.get("state_district") or components.get("county") or ""
                        state = components.get("state") or ""

                        return success_response(
                            data={
                                "village": village,
                                "district": district.replace(" District", ""),
                                "state": state
                            },
                            message="Location detected successfully",
                            status_code=status.HTTP_200_OK
                        )
            except Exception as e:
                logger.warning(f"OpenCage reverse geocode failed: {e}")

        # 2. Local Nearest Location lookup
        try:
            user_lat, user_lon = float(lat), float(lon)
            closest_city = None
            min_dist = float("inf")
            for city, (c_lat, c_lon) in KNOWN_LOCATIONS.items():
                d = haversine_distance(user_lat, user_lon, c_lat, c_lon)
                if d < min_dist:
                    min_dist = d
                    closest_city = city

            if closest_city and min_dist < 300:
                return success_response(
                    data={
                        "village": closest_city.title(),
                        "district": closest_city.title(),
                        "state": "Uttar Pradesh"
                    },
                    message="Location detected successfully",
                    status_code=status.HTTP_200_OK
                )
        except Exception:
            pass

        # 3. Try Nominatim (OpenStreetMap) fallback
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            res = requests.get(url, headers={"User-Agent": "AgroAISystem/1.0"}, timeout=2)
            if res.status_code == 200:
                data = res.json()
                address = data.get("address", {})
                village = (
                    address.get("village")
                    or address.get("town")
                    or address.get("city")
                    or address.get("suburb")
                    or address.get("county")
                    or ""
                )
                district = (
                    address.get("state_district")
                    or address.get("county")
                    or address.get("city_district")
                    or ""
                )
                state = address.get("state") or ""
                return success_response(
                    data={
                        "village": village,
                        "district": district.replace(" District", ""),
                        "state": state
                    },
                    message="Location detected successfully",
                    status_code=status.HTTP_200_OK
                )
        except Exception as e:
            logger.warning(f"Nominatim reverse geocode failed: {e}")

        return error_response(
            message="Location not found",
            error="Could not reverse geocode coordinates",
            status_code=status.HTTP_404_NOT_FOUND
        )
