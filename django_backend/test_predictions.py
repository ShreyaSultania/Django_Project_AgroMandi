import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agro_ai_backend.settings")
django.setup()

from predictions.ml import train_models, predict_price, predict_demand

def test():
    train_models()
    dps_input = {
        "cropQuality": 80,
        "price": 3000,
        "demand": 60,
        "weatherRisk": 0.2,
        "distance": 100,
        "transportAvailability": 80,
        "storageAvailability": 80,
    }

    print("Input:", dps_input)
    print("Predicted Price:", predict_price(dps_input))
    print("Predicted Demand:", predict_demand(dps_input))

if __name__ == "__main__":
    test()
