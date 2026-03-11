import numpy as np
from app.db.mongo_client import get_collection


def run_analytics(imei, metric, operation):

    collection = get_collection()

    data = list(collection.find({"imei": imei}))

    values = [x[metric] for x in data if metric in x]

    if operation == "avg":
        return np.mean(values)

    if operation == "max":
        return np.max(values)

    if operation == "min":
        return np.min(values)

    return None