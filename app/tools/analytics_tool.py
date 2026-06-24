import numpy as np

from app.db.mongoclient import get_collection
from app.utils.logger import logger


def run_analytics(imei, metric, operation):

    collection = get_collection()

    # if not collection:
    #     return 

    data = list(collection.find({"imei": imei}))

    values = [x.get(metric) for x in data if metric in x]
    # logger.info(f"Values got from {metric}: {values}")

    if not values:
        logger.warning(f"Empty result for IMEI: {imei}")
        return None

    if operation == "average":
        average = np.mean(values)
        logger.debug(f"Average: {average}")
        return {
            "type": "metric",
            "metric": metric,
            "aggregation": operation,
            "value": average
        }

    if operation == "maximum":
        maximum = np.max(values)
        logger.debug(f"Maximum: {maximum}")
        return {
            "type": "metric",
            "metric": metric,
            "aggregation": operation,
            "value": maximum
        }

    if operation == "minimum":
        minimum = np.min(values)
        logger.debug(f"Minimum: {minimum}")
        return {
            "type": "metric",
            "metric": metric,
            "aggregation": operation,
            "value": minimum
        }

    return None