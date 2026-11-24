import logging
from rest_framework.views import APIView
from rest_framework import status
from core.utils import success_response, error_response
from core.dps import calculate_dps
from core.mongodb import save_mongo_recommendation
from locations.utils import get_coordinates, haversine_distance
from weather.services import get_weather_risk
from predictions.ml import predict_price, predict_demand
from .services import (
    calculate_transport_cost,
    get_mandi_coordinates,
    fetch_mandi_prices,
)
from .models import Recommendation
from .serializers import RecommendationSerializer

logger = logging.getLogger(__name__)

DEFAULT_RADIUS_KM = 200

class RecommendMandiView(APIView):
    """
    POST /api/shipments/recommend-mandi?maxRadius=...
    Direct conversion of controllers/mandiController.js recommendMandi
    """
    def post(self, request):
        try:
            body = request.data or {}
            village = body.get("village", "").strip()
            district = body.get("district", "").strip()
            state_val = body.get("state", "").strip()
            commodity = body.get("commodity", "").strip()
            crop_quality = body.get("cropQuality", "B")
            transport_avail = body.get("transportAvailability", "rental")
            storage_avail = body.get("storageAvailability", "available")
            quantity = float(body.get("quantity", 10.0))

            try:
                max_radius = int(request.query_params.get("maxRadius", DEFAULT_RADIUS_KM))
            except (ValueError, TypeError):
                max_radius = DEFAULT_RADIUS_KM

            # Step 1: Geocode farmer's location
            farmer_coords = get_coordinates(village, district, state_val)
            if not farmer_coords:
                return error_response(
                    message="Could not locate farmer's village",
                    error="Geocoding failed",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Step 2: Fetch mandi prices
            mandi_records = fetch_mandi_prices(state_val, commodity)
            if not mandi_records:
                return error_response(
                    message="No mandi data found",
                    error=f"No mandis found for {commodity} in {state_val}",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Step 3: Deduplicate mandis (keep record with highest modal price)
            unique_mandis = {}
            for record in mandi_records:
                key = record.get("market") or record.get("Market")
                if not key:
                    continue
                try:
                    price = float(record.get("modal_price", 0))
                except (ValueError, TypeError):
                    price = 0.0

                if key not in unique_mandis:
                    unique_mandis[key] = record
                else:
                    existing_price = float(unique_mandis[key].get("modal_price", 0))
                    if price > existing_price:
                        unique_mandis[key] = record

            # Step 4: Geocode each mandi + filter by distance
            def geocode_and_filter(radius_km):
                results = []
                for record in unique_mandis.values():
                    market_name = record.get("market") or record.get("Market")
                    m_district = record.get("district") or record.get("District") or district
                    m_state = record.get("state") or record.get("State") or state_val

                    coords = get_mandi_coordinates(market_name, m_district, m_state)
                    if not coords:
                        continue

                    dist_km = haversine_distance(
                        farmer_coords["latitude"],
                        farmer_coords["longitude"],
                        coords["latitude"],
                        coords["longitude"]
                    )

                    if radius_km != float("inf") and dist_km > radius_km:
                        continue

                    item = dict(record)
                    item["latitude"] = coords["latitude"]
                    item["longitude"] = coords["longitude"]
                    item["distanceKm"] = round(dist_km, 1)
                    results.append(item)
                return results

            # Try requested radius, then progressively expand
            geocoded_mandis = geocode_and_filter(max_radius)
            effective_radius = max_radius

            if len(geocoded_mandis) == 0 and max_radius < 300:
                logger.info(f"No mandis within {max_radius}km, expanding to 300km...")
                geocoded_mandis = geocode_and_filter(300)
                effective_radius = 300

            if len(geocoded_mandis) == 0 and effective_radius < 600:
                logger.info("No mandis within 300km, expanding to 600km...")
                geocoded_mandis = geocode_and_filter(600)
                effective_radius = 600

            if len(geocoded_mandis) == 0:
                logger.info("No mandis within 600km, using 5 closest nationwide...")
                geocoded_mandis = geocode_and_filter(float("inf"))
                geocoded_mandis.sort(key=lambda x: x["distanceKm"])
                geocoded_mandis = geocoded_mandis[:5]
                effective_radius = None

            if len(geocoded_mandis) == 0:
                return error_response(
                    message="No mandi data available for this commodity",
                    error=f"No mandis found for {commodity} in the API data",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Step 5: Get weather risk once (same origin)
            weather_risk = get_weather_risk(farmer_coords["latitude"], farmer_coords["longitude"])

            # Step 6: Mappings for DPS and Transport Calculations
            transport_mapping = {"own": 100, "rental": 80, "limited": 40, "none": 0}
            try:
                num_transport_avail = float(transport_mapping.get(str(transport_avail).lower(), transport_avail))
            except (ValueError, TypeError):
                num_transport_avail = 50.0

            storage_mapping = {"available": 100, "limited": 50, "none": 0}
            try:
                num_storage_avail = float(storage_mapping.get(str(storage_avail).lower(), storage_avail))
            except (ValueError, TypeError):
                num_storage_avail = 50.0

            quality_mapping = {"A": 100, "B": 80, "C": 50, "D": 20}
            try:
                num_crop_quality = float(quality_mapping.get(str(crop_quality).upper(), crop_quality))
            except (ValueError, TypeError):
                num_crop_quality = 50.0

            # Step 7: Calculate DPS + net profit for each mandi
            evaluated_mandis = []
            for mandi in geocoded_mandis:
                try:
                    modal_price = float(mandi.get("modal_price", 0))
                except (ValueError, TypeError):
                    modal_price = 0.0

                try:
                    min_price = float(mandi.get("min_price", 0))
                except (ValueError, TypeError):
                    min_price = 0.0

                try:
                    max_price = float(mandi.get("max_price", 0))
                except (ValueError, TypeError):
                    max_price = 0.0

                distance_km = float(mandi.get("distanceKm", 0))
                transport_cost = calculate_transport_cost(distance_km, num_transport_avail)

                dps_input = {
                    "cropQuality": num_crop_quality,
                    "demand": min(modal_price / 25.0, 100.0),
                    "price": modal_price,
                    "weatherRisk": weather_risk,
                    "distance": distance_km,
                    "transportAvailability": num_transport_avail,
                    "storageAvailability": num_storage_avail,
                }

                pred_p = predict_price(dps_input)
                pred_d = predict_demand(dps_input)

                future_input = dict(dps_input)
                future_input["price"] = pred_p
                future_input["demand"] = pred_d

                dps_now = calculate_dps(dps_input)
                dps_later = calculate_dps(future_input)

                best_dps = max(dps_now, dps_later)
                decision = "Transport Now" if dps_now > dps_later else "Delay Shipment"
                net_profit = (modal_price * quantity) - transport_cost

                evaluated_mandis.append({
                    "mandiName": mandi.get("market") or mandi.get("Market"),
                    "district": mandi.get("district") or mandi.get("District") or district,
                    "distanceKm": distance_km,
                    "modalPrice": modal_price,
                    "minPrice": min_price,
                    "maxPrice": max_price,
                    "transportCost": transport_cost,
                    "netProfit": net_profit,
                    "dpsNow": round(dps_now, 2),
                    "dpsLater": round(dps_later, 2),
                    "bestDPS": round(best_dps, 2),
                    "decision": decision,
                    "predictedPrice": round(pred_p, 2),
                    "predictedDemand": round(pred_d, 2),
                })

            # Step 8: Rank by DPS score descending
            evaluated_mandis.sort(key=lambda x: x["bestDPS"], reverse=True)

            ranked_mandis = []
            for idx, m in enumerate(evaluated_mandis):
                item = dict(m)
                item["rank"] = idx + 1
                ranked_mandis.append(item)

            # Step 9: Return response
            return success_response(
                data={
                    "farmerLocation": {
                        "village": village,
                        "district": district,
                        "state": state_val,
                        "latitude": farmer_coords["latitude"],
                        "longitude": farmer_coords["longitude"],
                    },
                    "commodity": commodity,
                    "searchRadiusKm": effective_radius if effective_radius is not None else "nationwide",
                    "radiusExpanded": effective_radius != max_radius,
                    "totalMandisFound": len(ranked_mandis),
                    "recommendation": ranked_mandis[0] if ranked_mandis else None,
                    "allMandis": ranked_mandis,
                },
                message="Mandi recommendations generated successfully",
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Mandi recommendation error: {e}", exc_info=True)
            return error_response(
                message="Failed to generate mandi recommendations",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmMandiView(APIView):
    """
    POST /api/shipments/confirm-mandi
    Direct conversion of controllers/mandiController.js confirmMandi
    """
    def post(self, request):
        try:
            body = request.data or {}

            # Handle both nested payload and flat payload
            farmer_loc = body.get("farmerLocation")
            selected_mandi = body.get("selectedMandi")

            if not farmer_loc:
                farmer_loc = {
                    "village": body.get("village", ""),
                    "district": body.get("district", ""),
                    "state": body.get("state", ""),
                    "latitude": body.get("latitude"),
                    "longitude": body.get("longitude"),
                }

            if not selected_mandi:
                selected_mandi = {
                    "mandiName": body.get("mandiName", ""),
                    "district": body.get("mandiDistrict") or body.get("district", ""),
                    "modalPrice": body.get("modalPrice", 0),
                    "transportCost": body.get("transportCost", 0),
                    "netProfit": body.get("netProfit", 0),
                    "decision": body.get("decision", "Transport Now"),
                    "distanceKm": body.get("distanceKm", 0),
                    "bestDPS": body.get("bestDPS", 0),
                    "rank": body.get("rank", 1),
                }

            commodity = body.get("commodity", "")
            if not farmer_loc.get("village") or not commodity or not selected_mandi.get("mandiName"):
                return error_response(
                    message="Missing required fields",
                    error="farmerLocation, commodity, and selectedMandi are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            quantity = float(body.get("quantity", 10.0))
            crop_quality = str(body.get("cropQuality", "80"))

            recommendation = Recommendation.objects.create(
                farmer_village=farmer_loc.get("village", ""),
                farmer_district=farmer_loc.get("district", ""),
                farmer_state=farmer_loc.get("state", ""),
                farmer_latitude=farmer_loc.get("latitude"),
                farmer_longitude=farmer_loc.get("longitude"),
                commodity=commodity,
                quantity=quantity,
                crop_quality=crop_quality,
                selected_mandi_name=selected_mandi.get("mandiName", ""),
                selected_mandi_district=selected_mandi.get("district", ""),
                distance_km=float(selected_mandi.get("distanceKm", 0)),
                modal_price=float(selected_mandi.get("modalPrice", 0)),
                min_price=float(selected_mandi.get("minPrice")) if selected_mandi.get("minPrice") is not None else None,
                max_price=float(selected_mandi.get("maxPrice")) if selected_mandi.get("maxPrice") is not None else None,
                transport_cost=float(selected_mandi.get("transportCost", 0)),
                net_profit=float(selected_mandi.get("netProfit", 0)),
                dps_now=float(selected_mandi.get("dpsNow")) if selected_mandi.get("dpsNow") is not None else None,
                dps_later=float(selected_mandi.get("dpsLater")) if selected_mandi.get("dpsLater") is not None else None,
                best_dps=float(selected_mandi.get("bestDPS", 0)),
                decision=selected_mandi.get("decision", "Transport Now"),
                rank=int(selected_mandi.get("rank", 1)),
                weather_risk=float(body.get("weatherRisk")) if body.get("weatherRisk") is not None else None,
                transport_availability=str(body.get("transportAvailability")) if body.get("transportAvailability") is not None else None,
                storage_availability=str(body.get("storageAvailability")) if body.get("storageAvailability") is not None else None,
                total_mandis_evaluated=int(body.get("totalMandisEvaluated")) if body.get("totalMandisEvaluated") is not None else None,
                raw_details=body
            )

            # Also persist to MongoDB Atlas recommendations collection
            mongo_payload = {
                "farmerLocation": farmer_loc,
                "commodity": commodity,
                "quantity": quantity,
                "cropQuality": crop_quality,
                "selectedMandi": selected_mandi,
                "weatherRisk": body.get("weatherRisk"),
                "transportAvailability": body.get("transportAvailability"),
                "storageAvailability": body.get("storageAvailability"),
                "totalMandisEvaluated": body.get("totalMandisEvaluated"),
                "status": "confirmed",
            }
            save_mongo_recommendation(mongo_payload)

            serializer = RecommendationSerializer(recommendation)
            return success_response(
                data={"recommendation": serializer.data},
                message="Mandi selection confirmed and saved",
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Confirm mandi error: {e}", exc_info=True)
            return error_response(
                message="Failed to confirm mandi selection",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
