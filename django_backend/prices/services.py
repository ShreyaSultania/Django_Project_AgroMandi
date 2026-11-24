import os
import csv
import json
import logging
import requests
from django.conf import settings
from locations.utils import is_valid_api_key

logger = logging.getLogger(__name__)

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

TARGET_COMMODITIES = [
    "Wheat", "Rice", "Maize", "Bajra", "Gram", "Soybean",
    "Cotton", "Groundnut", "Mustard", "Onion", "Potato", "Tomato"
]

_memory_cache = {}

def get_redis_client():
    redis_uri = os.getenv("REDIS_URI", "").strip()
    if not is_valid_api_key(redis_uri):
        return None
    try:
        import redis
        client = redis.from_url(redis_uri, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None

def read_records_from_csv(commodity_filter=None, max_records=2000):
    csv_path = settings.BASE_DIR / "data" / "9ef84268-d588-465a-a308-a864a43d0070.csv"
    if not csv_path.exists():
        logger.warning(f"CSV file not found at {csv_path}")
        return []

    records = []
    try:
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                comm = row.get("Commodity", "")
                if commodity_filter:
                    if commodity_filter.lower() not in comm.lower():
                        continue

                record = {
                    "market": row.get("Market", ""),
                    "district": row.get("District", ""),
                    "state": row.get("State", ""),
                    "commodity": comm,
                    "variety": row.get("Variety", ""),
                    "arrival_date": row.get("Arrival_Date", ""),
                    "min_price": row.get("Min_x0020_Price", "0"),
                    "max_price": row.get("Max_x0020_Price", "0"),
                    "modal_price": row.get("Modal_x0020_Price", "0"),
                }
                records.append(record)
                if len(records) >= max_records:
                    break
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")

    return records

def fetch_latest_prices_service(max_records=2000):
    api_key = os.getenv("DATA_GOV_API_KEY", "").strip()

    if is_valid_api_key(api_key):
        try:
            res = requests.get(
                BASE_URL,
                params={
                    "api-key": api_key,
                    "format": "json",
                    "limit": max_records,
                },
                timeout=3
            )
            if res.status_code == 200:
                data = res.json()
                records = data.get("records", [])
                if records:
                    return records
        except Exception as e:
            logger.warning(f"Error fetching from data.gov.in: {e}. Falling back to CSV.")

    return read_records_from_csv(max_records=max_records)
