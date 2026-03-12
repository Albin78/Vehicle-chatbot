import numpy as np

from app.db.mongoclient import get_collection
from app.utils.logger import logger


def run_analytics(imei, metric, operation):

    collection = get_collection()

    data = list(collection.find({"imei": imei}))

    values = [x[metric] for x in data if metric in x]

    if not values:
        # logger.error("Empty result for IMEI: %s", imei)
        print("Empty result for IMEI: ", imei)
        return None

    if operation == "avg":
        return np.mean(values)

    if operation == "max":
        return np.max(values)

    if operation == "min":
        return np.min(values)

    return None