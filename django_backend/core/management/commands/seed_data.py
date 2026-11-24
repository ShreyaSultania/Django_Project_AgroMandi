from django.core.management.base import BaseCommand
from core.models import Config
from mandis.models import Mandi
from locations.utils import KNOWN_LOCATIONS
from predictions.ml import train_models

class Command(BaseCommand):
    help = "Seeds initial database configuration and pre-trains ML models"

    def handle(self, *args, **options):
        self.stdout.write("Seeding default Config weights...")
        config, created = Config.objects.get_or_create(
            id=1,
            defaults={
                "crop_quality": 0.2,
                "demand": 0.2,
                "price": 0.3,
                "weather_risk": 0.15,
                "distance": 0.1,
                "transport_availability": 0.1,
                "storage_availability": 0.05
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created default Config weights."))
        else:
            self.stdout.write("Default Config weights already exist.")

        self.stdout.write("Pre-caching known mandi coordinates...")
        count = 0
        for city, (lat, lon) in KNOWN_LOCATIONS.items():
            name = f"{city.title()} APMC"
            mandi, created = Mandi.objects.get_or_create(
                name=name,
                state="Uttar Pradesh" if city in ["agra", "varanasi", "lucknow", "kanpur", "mirzapur"] else "India",
                defaults={
                    "district": city.title(),
                    "latitude": lat,
                    "longitude": lon,
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Pre-cached {count} known mandi locations."))

        self.stdout.write("Training ML models...")
        train_models()
        self.stdout.write(self.style.SUCCESS("ML models trained successfully."))
