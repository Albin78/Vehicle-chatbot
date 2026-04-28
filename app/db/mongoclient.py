from pymongo import MongoClient
from app.config import settings
from app.utils.logger import logger

client = MongoClient(settings.MONGO_URI)
print(f"Mongo Client: {client}")
db = client[settings.MONGO_DB]


def get_collection():
    return db[settings.MONGO_COLLECTION]


def get_db_fields():
    collection = get_collection()
    logger.info(f"Mongo collection: {collection}")

    sample = collection.find_one()

    if not sample:
        logger.warning("No documents found in collection")
        return []

    excluded = {"_id", "imei", "date", "sensor", "moving_time", "last_updated"}
    fields = [k for k in sample.keys() if k not in excluded]
    logger.info(f"Fields available: {fields}")

    return fields
