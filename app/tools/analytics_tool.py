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
        # logger.error("Empty result for IMEI: %s", imei)
        print("Empty result for IMEI: ", imei)
        return None

    if operation == "average":
        average = np.mean(values)
        print("Average: ", average)
        # average_in_volt = np.round(average / 1000, 2)
        # print("Average in Volt: ", average_in_volt)
        return average

    if operation == "maximum":
        maximum = np.max(values)
        print("Maximum: ", maximum)
        return maximum

    if operation == "minimum":
        minimum = np.min(values)
        print("Minimum: ", minimum)
        return minimum

    return None