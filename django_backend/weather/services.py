import os
import requests
import logging
from locations.utils import is_valid_api_key

logger = logging.getLogger(__name__)

def get_weather_risk(lat, lon):
    """
    Direct conversion of services/weatherService.js
    """
    api_key = os.getenv("WEATHER_API_KEY", "").strip()

    if not is_valid_api_key(api_key):
        return 50.0

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        res = requests.get(url, timeout=3)
        if res.status_code != 200:
            return 50.0

        weather = res.json()
        risk = 30.0

        weather_list = weather.get("weather", [])
        if weather_list and weather_list[0].get("main") == "Rain":
            risk += 40.0

        main = weather.get("main", {})
        temp = main.get("temp", 25)
        if temp > 35:
            risk += 30.0
        elif temp < 10:
            risk += 20.0

        humidity = main.get("humidity", 50)
        wind_speed = weather.get("wind", {}).get("speed", 5)

        if humidity > 80:
            risk += 10.0
        if wind_speed > 10:
            risk += 10.0

        return min(risk, 100.0)
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return 50.0

def get_fallback_weather(city_or_loc="New Delhi"):
    city_name = city_or_loc if city_or_loc else "Delhi"
    return {
        "coord": {"lon": 77.209, "lat": 28.6139},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
        "base": "stations",
        "main": {
            "temp": 28.5,
            "feels_like": 29.0,
            "temp_min": 26.0,
            "temp_max": 31.0,
            "pressure": 1012,
            "humidity": 55
        },
        "visibility": 10000,
        "wind": {"speed": 3.6, "deg": 120},
        "clouds": {"all": 0},
        "dt": 1713780000,
        "sys": {"type": 1, "id": 9165, "country": "IN", "sunrise": 1713745200, "sunset": 1713792000},
        "timezone": 19800,
        "id": 1273294,
        "name": city_name,
        "cod": 200
    }

def get_fallback_forecast(city_or_loc="New Delhi"):
    city_name = city_or_loc if city_or_loc else "Delhi"
    forecast_list = []
    days = ["2026-04-22", "2026-04-23", "2026-04-24", "2026-04-25", "2026-04-26"]
    for day in days:
        for hour in ["00:00:00", "06:00:00", "12:00:00", "18:00:00"]:
            forecast_list.append({
                "dt": 1713780000,
                "main": {
                    "temp": 29.0,
                    "temp_min": 24.0,
                    "temp_max": 33.0,
                    "humidity": 50
                },
                "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
                "pop": 0.1,
                "dt_txt": f"{day} {hour}"
            })
    return {
        "cod": "200",
        "message": 0,
        "cnt": len(forecast_list),
        "list": forecast_list,
        "city": {
            "id": 1273294,
            "name": city_name,
            "country": "IN"
        }
    }
