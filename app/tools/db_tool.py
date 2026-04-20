from app.db.mongoclient import get_collection
from app.utils.logger import logger

def fetch_telemetry(imei, metric):

    collection = get_collection()

    result = collection.find_one(
        {"imei": imei},
        sort=[("last_updated", -1)]
    )
    
    logger.info(f"Result: {result}")
    # print("Result: ", result)
    if result:
        value = result.get(metric)
        return {
            "type": "metric",
            "metric": metric,
            "value": value
        }
    
    return None