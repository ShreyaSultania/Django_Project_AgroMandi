from django.core.management.base import BaseCommand
from core.mongodb import get_mongo_db
from core.models import Config
from mandis.models import Mandi, Recommendation

class Command(BaseCommand):
    help = "Syncs existing records (Configs, Mandis, Recommendations) from MongoDB Atlas into Django ORM"

    def handle(self, *args, **options):
        db = get_mongo_db()
        if db is None:
            self.stdout.write(self.style.ERROR("Could not connect to MongoDB Atlas. Check MONGO_URI in .env"))
            return

        self.stdout.write(self.style.SUCCESS(f"Connected to MongoDB Atlas: {db.name}"))

        # 1. Sync Config
        cfg_doc = db["configs"].find_one()
        if cfg_doc:
            Config.objects.update_or_create(
                id=1,
                defaults={
                    "crop_quality": float(cfg_doc.get("cropQuality", 0.3)),
                    "demand": float(cfg_doc.get("demand", 0.25)),
                    "price": float(cfg_doc.get("price", 0.2)),
                    "weather_risk": float(cfg_doc.get("weatherRisk", 0.15)),
                    "distance": float(cfg_doc.get("distance", 0.1)),
                    "transport_availability": float(cfg_doc.get("transportAvailability", 0.1)),
                    "storage_availability": float(cfg_doc.get("storageAvailability", 0.2)),
                }
            )
            self.stdout.write(self.style.SUCCESS("Synced Config weights from MongoDB."))

        # 2. Sync Mandis
        mandi_docs = list(db["mandis"].find())
        self.stdout.write(f"Found {len(mandi_docs)} mandis in MongoDB Atlas. Syncing...")
        created_count = 0
        updated_count = 0

        for doc in mandi_docs:
            name = doc.get("name")
            state = doc.get("state")
            district = doc.get("district", "")
            lat = doc.get("latitude")
            lon = doc.get("longitude")

            if not name or not state or lat is None or lon is None:
                continue

            obj, created = Mandi.objects.update_or_create(
                name=name,
                state=state,
                defaults={
                    "district": district,
                    "latitude": float(lat),
                    "longitude": float(lon),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Mandis sync complete! Created: {created_count}, Updated: {updated_count} (Total in DB: {Mandi.objects.count()})"))

        # 3. Sync Recommendations
        rec_docs = list(db["recommendations"].find())
        self.stdout.write(f"Found {len(rec_docs)} recommendations in MongoDB Atlas. Syncing...")
        rec_count = 0
        for doc in rec_docs:
            farmer_loc = doc.get("farmerLocation", {})
            selected = doc.get("selectedMandi", {})
            commodity = doc.get("commodity", "")
            if not commodity or not selected.get("mandiName"):
                continue

            Recommendation.objects.get_or_create(
                farmer_village=farmer_loc.get("village", ""),
                farmer_district=farmer_loc.get("district", ""),
                farmer_state=farmer_loc.get("state", ""),
                commodity=commodity,
                selected_mandi_name=selected.get("mandiName", ""),
                defaults={
                    "farmer_latitude": farmer_loc.get("latitude"),
                    "farmer_longitude": farmer_loc.get("longitude"),
                    "quantity": float(doc.get("quantity", 10)),
                    "crop_quality": str(doc.get("cropQuality", "60")),
                    "selected_mandi_district": selected.get("district", ""),
                    "distance_km": float(selected.get("distanceKm", 0)),
                    "modal_price": float(selected.get("modalPrice", 0)),
                    "min_price": float(selected.get("minPrice")) if selected.get("minPrice") is not None else None,
                    "max_price": float(selected.get("maxPrice")) if selected.get("maxPrice") is not None else None,
                    "transport_cost": float(selected.get("transportCost", 0)),
                    "net_profit": float(selected.get("netProfit", 0)),
                    "dps_now": float(selected.get("dpsNow")) if selected.get("dpsNow") is not None else None,
                    "dps_later": float(selected.get("dpsLater")) if selected.get("dpsLater") is not None else None,
                    "best_dps": float(selected.get("bestDPS", 0)),
                    "decision": selected.get("decision", "Transport Now"),
                    "rank": int(selected.get("rank", 1)),
                    "weather_risk": float(doc.get("weatherRisk")) if doc.get("weatherRisk") is not None else None,
                    "transport_availability": str(doc.get("transportAvailability")) if doc.get("transportAvailability") is not None else None,
                    "storage_availability": str(doc.get("storageAvailability")) if doc.get("storageAvailability") is not None else None,
                    "total_mandis_evaluated": int(doc.get("totalMandisEvaluated")) if doc.get("totalMandisEvaluated") is not None else None,
                    "status": doc.get("status", "confirmed"),
                }
            )
            rec_count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {rec_count} recommendations."))
