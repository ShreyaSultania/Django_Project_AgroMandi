import json
import logging
from rest_framework.views import APIView
from rest_framework import status
from core.utils import success_response, error_response
from .services import (
    TARGET_COMMODITIES,
    get_redis_client,
    fetch_latest_prices_service,
    _memory_cache
)

logger = logging.getLogger(__name__)

CACHE_KEY = "latest_market_prices"

class PricesView(APIView):
    """
    GET /api/prices
    Direct conversion of controllers/priceController.js
    """
    def get(self, request):
        try:
            redis_client = get_redis_client()

            # 1. Try to get from Cache
            if redis_client:
                try:
                    cached = redis_client.get(CACHE_KEY)
                    if cached:
                        prices = json.loads(cached)
                        return success_response(
                            data={"prices": prices},
                            message="Latest prices fetched successfully (Cached)",
                            status_code=status.HTTP_200_OK
                        )
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")
            elif CACHE_KEY in _memory_cache:
                return success_response(
                    data={"prices": _memory_cache[CACHE_KEY]},
                    message="Latest prices fetched successfully (Cached)",
                    status_code=status.HTTP_200_OK
                )

            # 2. Fetch prices from Service
            records = fetch_latest_prices_service(max_records=2000)

            commodity_map = {
                c: {"total": 0.0, "count": 0, "min": float("inf"), "max": float("-inf")}
                for c in TARGET_COMMODITIES
            }

            for record in records:
                comm_name = record.get("commodity", "")
                if not comm_name:
                    continue

                for target in TARGET_COMMODITIES:
                    if target.lower() in comm_name.lower():
                        try:
                            price = float(record.get("modal_price", 0))
                            if price > 0:
                                commodity_map[target]["total"] += price
                                commodity_map[target]["count"] += 1
                                if price < commodity_map[target]["min"]:
                                    commodity_map[target]["min"] = price
                                if price > commodity_map[target]["max"]:
                                    commodity_map[target]["max"] = price
                        except (ValueError, TypeError):
                            pass
                        break

            prices = []
            for c in TARGET_COMMODITIES:
                data = commodity_map[c]
                avg_price = round(data["total"] / data["count"]) if data["count"] > 0 else 0
                mock_change = ((len(c) * 7) % 11) - 4
                min_p = data["min"] if data["min"] != float("inf") else 0
                max_p = data["max"] if data["max"] != float("-inf") else 0

                if avg_price > 0:
                    prices.append({
                        "name": c,
                        "price": avg_price,
                        "change": mock_change,
                        "min": min_p,
                        "max": max_p,
                    })

            # 3. Save to Cache
            if redis_client:
                try:
                    redis_client.setex(CACHE_KEY, 3600, json.dumps(prices))
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
            else:
                _memory_cache[CACHE_KEY] = prices

            return success_response(
                data={"prices": prices},
                message="Latest prices fetched successfully",
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            return error_response(
                message="Failed to fetch prices",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
