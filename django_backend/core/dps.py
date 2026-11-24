from core.models import Config
from core.mongodb import get_mongo_config

def calculate_dps(data):
    """
    Direct conversion of services/dpsService.js:
    weights.cropQuality * data.cropQuality +
    weights.demand * data.demand +
    weights.price * data.price -
    weights.weatherRisk * data.weatherRisk -
    weights.distance * data.distance +
    weights.transportAvailability * data.transportAvailability -
    weights.storageAvailability * data.storageAvailability
    """
    mongo_cfg = get_mongo_config()

    if mongo_cfg:
        w_crop_quality = float(mongo_cfg.get("cropQuality", 0.3))
        w_demand = float(mongo_cfg.get("demand", 0.25))
        w_price = float(mongo_cfg.get("price", 0.2))
        w_weather_risk = float(mongo_cfg.get("weatherRisk", 0.15))
        w_distance = float(mongo_cfg.get("distance", 0.1))
        w_transport = float(mongo_cfg.get("transportAvailability", 0.1))
        w_storage = float(mongo_cfg.get("storageAvailability", 0.2))
    else:
        config = Config.get_config()
        w_crop_quality = config.crop_quality
        w_demand = config.demand
        w_price = config.price
        w_weather_risk = config.weather_risk
        w_distance = config.distance
        w_transport = config.transport_availability
        w_storage = config.storage_availability

    crop_quality = float(data.get("cropQuality", 50))
    demand = float(data.get("demand", 50))
    price = float(data.get("price", 0))
    weather_risk = float(data.get("weatherRisk", 50))
    distance = float(data.get("distance", 0))
    transport_availability = float(data.get("transportAvailability", 50))
    storage_availability = float(data.get("storageAvailability", 50))

    score = (
        w_crop_quality * crop_quality
        + w_demand * demand
        + w_price * price
        - w_weather_risk * weather_risk
        - w_distance * distance
        + w_transport * transport_availability
        - w_storage * storage_availability
    )
    return score
