from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB")]
collection = db[os.getenv("MONGO_COLLECTION")]

# Ensure index exists (safe to call multiple times)
collection.create_index([("imei", 1), ("last_updated", 1)])

imei = 354018114615747

start = time.time()
print("Starting Mongo fetch")

cursor = collection.find({"imei": imei}) \
                   .sort("last_updated", 1)

for record in cursor:
    pass   # process here

print("Mongo fetch done")
print("Time taken: ", time.time() - start)