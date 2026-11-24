import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_mongo_client = None
_mongo_db = None

def get_mongo_db():
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if not mongo_uri or mongo_uri.startswith("your_"):
        return None

    try:
        import pymongo
        _mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=4000)
        # Test connection
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client.get_database()
        logger.info(f"Connected to MongoDB Atlas database: {_mongo_db.name}")
        return _mongo_db
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB: {e}")
        return None

def get_mongo_config():
    db = get_mongo_db()
    if db is None:
        return None
    try:
        cfg = db["configs"].find_one()
        if cfg:
            cfg.pop("_id", None)
            return cfg
    except Exception as e:
        logger.warning(f"Error fetching config from MongoDB: {e}")
    return None

def get_mongo_mandi(name, state):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        mandi = db["mandis"].find_one({"name": name, "state": state})
        if mandi and "latitude" in mandi and "longitude" in mandi:
            return {"latitude": mandi["latitude"], "longitude": mandi["longitude"]}
    except Exception as e:
        logger.warning(f"Error reading mandi from MongoDB: {e}")
    return None

def save_mongo_mandi(name, district, state, latitude, longitude):
    db = get_mongo_db()
    if db is None:
        return
    try:
        db["mandis"].update_one(
            {"name": name, "state": state},
            {"$set": {
                "name": name,
                "district": district,
                "state": state,
                "latitude": latitude,
                "longitude": longitude,
                "lastUpdated": datetime.now(),
                "updatedAt": datetime.now()
            }},
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Error saving mandi to MongoDB: {e}")

def save_mongo_recommendation(data):
    db = get_mongo_db()
    if db is None:
        return
    try:
        doc = dict(data)
        doc["createdAt"] = datetime.now()
        doc["updatedAt"] = datetime.now()
        db["recommendations"].insert_one(doc)
    except Exception as e:
        logger.warning(f"Error saving recommendation to MongoDB: {e}")
