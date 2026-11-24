import json
import logging
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from django.conf import settings

logger = logging.getLogger(__name__)

price_model = None
demand_model = None
is_trained = False

def train_models():
    global price_model, demand_model, is_trained
    if is_trained:
        return

    try:
        data_path = settings.BASE_DIR / "data" / "synthetic_training_data.json"
        if not data_path.exists():
            logger.warning(f"Training data not found at {data_path}. Using heuristics.")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        X = []
        y_price = []
        y_demand = []

        for row in data:
            X.append([
                float(row["cropQuality"]),
                float(row["price"]),
                float(row["demand"]),
                float(row["weatherRisk"]),
                float(row["distance"]),
                float(row["transportAvailability"]),
                float(row["storageAvailability"]),
            ])
            y_price.append(float(row["futurePrice"]))
            y_demand.append(float(row["futureDemand"]))

        rf_options = {
            "n_estimators": 20,
            "max_features": 3,
            "random_state": 42
        }

        pm = RandomForestRegressor(**rf_options)
        pm.fit(X, y_price)

        dm = RandomForestRegressor(**rf_options)
        dm.fit(X, y_demand)

        price_model = pm
        demand_model = dm
        is_trained = True
        logger.info(f"ML Models trained successfully with {len(X)} records.")
    except Exception as e:
        logger.error(f"Error training ML models: {e}")

def extract_features(data):
    return [
        float(data.get("cropQuality", 50)),
        float(data.get("price", 2000)),
        float(data.get("demand", 50)),
        float(data.get("weatherRisk", 50)),
        float(data.get("distance", 50)),
        float(data.get("transportAvailability", 50)),
        float(data.get("storageAvailability", 50)),
    ]

def predict_price(data):
    if not is_trained:
        train_models()

    price = float(data.get("price", 2000))
    weather_risk = float(data.get("weatherRisk", 50))

    if price_model is None:
        risk_premium = weather_risk * 0.1 * price
        return max(0.0, price + risk_premium)

    try:
        feats = extract_features(data)
        pred = price_model.predict([feats])[0]
        return max(0.0, float(pred))
    except Exception as e:
        logger.warning(f"Price prediction error: {e}")
        return price

def predict_demand(data):
    if not is_trained:
        train_models()

    demand = float(data.get("demand", 50))
    crop_quality = float(data.get("cropQuality", 50))

    if demand_model is None:
        return max(1.0, min(100.0, demand + (crop_quality / 10.0)))

    try:
        feats = extract_features(data)
        pred = demand_model.predict([feats])[0]
        return max(1.0, min(100.0, float(pred)))
    except Exception as e:
        logger.warning(f"Demand prediction error: {e}")
        return demand
