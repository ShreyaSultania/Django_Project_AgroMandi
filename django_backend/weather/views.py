import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from locations.utils import is_valid_api_key
from .services import get_fallback_weather, get_fallback_forecast

logger = logging.getLogger(__name__)

class WeatherView(APIView):
    """
    GET /api/weather?city=... OR ?lat=...&lon=...
    Direct conversion of controllers/weatherController.js
    """
    def get(self, request):
        city = request.query_params.get("city")
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not city and (not lat or not lon):
            return Response(
                {"success": False, "message": "City or Lat/Lon is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        api_key = os.getenv("WEATHER_API_KEY", "").strip()

        if not is_valid_api_key(api_key):
            loc_label = city or f"Coords ({lat}, {lon})"
            return Response({
                "success": True,
                "current": get_fallback_weather(loc_label),
                "forecast": get_fallback_forecast(loc_label)
            }, status=status.HTTP_200_OK)

        try:
            if lat and lon:
                current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            else:
                current_url = f"https://api.openweathermap.org/data/2.5/weather?q={requests.utils.quote(city)}&appid={api_key}&units=metric"
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={requests.utils.quote(city)}&appid={api_key}&units=metric"

            current_res = requests.get(current_url, timeout=3)
            forecast_res = requests.get(forecast_url, timeout=3)

            if current_res.status_code != 200 or forecast_res.status_code != 200:
                loc_label = city or f"Coords ({lat}, {lon})"
                return Response({
                    "success": True,
                    "current": get_fallback_weather(loc_label),
                    "forecast": get_fallback_forecast(loc_label)
                }, status=status.HTTP_200_OK)

            return Response({
                "success": True,
                "current": current_res.json(),
                "forecast": forecast_res.json()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            loc_label = city or "Current Location"
            return Response({
                "success": True,
                "current": get_fallback_weather(loc_label),
                "forecast": get_fallback_forecast(loc_label)
            }, status=status.HTTP_200_OK)
