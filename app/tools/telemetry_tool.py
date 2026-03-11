from app.db.mongo_client import get_collection


def fetch_telemetry(imei, metric):

    collection = get_collection()

    result = collection.find_one(
        {"imei": imei},
        sort=[("last_updated", -1)]
    )

    return result.get(metric)