import os
import re
import logging
import requests
from django.conf import settings
from .models import Mandi
from locations.utils import get_coordinates, is_valid_api_key
from prices.services import read_records_from_csv
from core.mongodb import get_mongo_mandi, save_mongo_mandi

logger = logging.getLogger(__name__)

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

def calculate_transport_cost(distance_km, transport_availability):
    """
    Direct conversion of utils/transportCost.js:
    const baseCostPerKm = 15;
    const availabilityFactor = 1 + (100 - transportAvailability) / 100;
    return Math.round(distanceKm * baseCostPerKm * availabilityFactor);
    """
    base_cost_per_km = 15.0
    availability_factor = 1.0 + (100.0 - float(transport_availability)) / 100.0
    return round(float(distance_km) * base_cost_per_km * availability_factor)

def get_mandi_coordinates(mandi_name, district, state):
    """
    Checks Django ORM cache first, then MongoDB Atlas collection,
    then geocodes via OpenCage/Nominatim and caches in both.
    """
    clean_name = re.sub(r'\s+(APMC|apmc|Yard|yard|Mandi|mandi)\s*$', '', mandi_name, flags=re.IGNORECASE).strip()

    # 1. Check Django ORM cache first
    cached = Mandi.objects.filter(name=mandi_name, state=state).first()
    if cached:
        return {"latitude": cached.latitude, "longitude": cached.longitude}

    # 2. Check MongoDB Atlas collection
    mongo_coords = get_mongo_mandi(mandi_name, state)
    if mongo_coords:
        try:
            Mandi.objects.update_or_create(
                name=mandi_name,
                state=state,
                defaults={
                    "district": district,
                    "latitude": mongo_coords["latitude"],
                    "longitude": mongo_coords["longitude"],
                }
            )
        except Exception:
            pass
        return mongo_coords

    # 3. Geocode clean name
    coords = get_coordinates(clean_name, district, state)
    if not coords:
        return None

    # 4. Save to Django ORM cache
    try:
        Mandi.objects.update_or_create(
            name=mandi_name,
            state=state,
            defaults={
                "district": district,
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            }
        )
    except Exception as e:
        logger.warning(f"Mandi ORM cache save error: {e}")

    # 5. Save to MongoDB Atlas collection
    save_mongo_mandi(mandi_name, district, state, coords["latitude"], coords["longitude"])

    return coords

_mandi_prices_cache = {}

def fetch_mandi_prices(state, commodity):
    """
    Direct conversion of fetchMandiPrices in services/mandiService.js
    Includes in-memory caching and resilient fallback to local CSV dataset.
    """
    cache_key = f"{str(state).strip().lower()}_{str(commodity).strip().lower()}"
    if cache_key in _mandi_prices_cache:
        return _mandi_prices_cache[cache_key]

    api_key = os.getenv("DATA_GOV_API_KEY", "").strip()

    if is_valid_api_key(api_key):
        try:
            all_records = []
            offset = 0
            limit = 100
            has_more = True

            while has_more:
                res = requests.get(
                    BASE_URL,
                    params={
                        "api-key": api_key,
                        "format": "json",
                        "limit": limit,
                        "offset": offset,
                        "filters[commodity]": commodity,
                    },
                    timeout=2.0
                )
                if res.status_code != 200:
                    break

                data = res.json()
                records = data.get("records", [])
                total = data.get("total", 0)

                if not records:
                    break

                all_records.extend(records)
                offset += limit
                has_more = len(all_records) < total and len(all_records) < 2000

            if all_records:
                logger.info(f"Fetched {len(all_records)} mandi records for {commodity} from API")
                _mandi_prices_cache[cache_key] = all_records
                return all_records
        except Exception as e:
            logger.warning(f"Error fetching mandi prices from API: {e}. Falling back to CSV.")

    # Fallback to local Agmarknet CSV dataset
    csv_records = read_records_from_csv(commodity_filter=commodity, max_records=2000)
    if csv_records:
        _mandi_prices_cache[cache_key] = csv_records
    return csv_records
