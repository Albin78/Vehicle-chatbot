from pymongo import MongoClient
from app.config import settings

client = MongoClient(settings.MONGO_URI)
print(f"Mongo Client: {client}")
db = client[settings.MONGO_DB]


def get_collection():
    return db[settings.MONGO_COLLECTION]