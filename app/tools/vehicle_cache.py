# vehicle_cache.py
from app.tools.external_api_tool import get_vehicle_details
from app.utils.logger import logger
import time


vehicle_cache = {
    "data": None,
    "imei_map": {},
    "last_updated": None
}


CACHE_TTL = 300  # 5 minutes

def load_vehicle_cache():
    current_time = time.time()

    if (
        vehicle_cache["data"] is None or
        (current_time - vehicle_cache["last_updated"]) > CACHE_TTL
    ):
        logger.info("[CACHE MISS] Reloading from API")

        response = get_vehicle_details()
        vehicle_list = response.get("VehicleList", [])

        imei_map = {
            str(v.get("IMEI")).strip(): v
            for v in vehicle_list
            if isinstance(v, dict) and v.get("IMEI")
        }

        vehicle_cache["data"] = vehicle_list
        vehicle_cache["imei_map"] = imei_map
        vehicle_cache["last_updated"] = current_time

        logger.info(f"[CACHE BUILT] {len(imei_map)} vehicles loaded")

    else:
        logger.info("[CACHE HIT] Using existing cache")

    return vehicle_cache


def get_vehicle_from_cache(imei):
    cache = load_vehicle_cache()
    return cache["imei_map"].get(str(imei))


def resolve_intent(intent):
    # HARD GUARANTEES (production-safe)

    if intent.metric is not None:
        intent.service = None

    elif intent.aggregation is not None:
        intent.service = None

    elif intent.imei is not None:
        intent.service = "vehicle_service"

    else:
        intent.service = None

    return intent