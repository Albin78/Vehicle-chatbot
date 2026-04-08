# vehicle_cache.py
from app.tools.external_api_tool import get_vehicle_details
from app.utils.logger import logger
import time


vehicle_cache = {
    "data": None,
    "vehicle_map": {},
    "last_updated": None
}


CACHE_TTL = 300  # 5 minutes

def load_vehicle_cache(company_id):
    current_time = time.time()

    if (
        vehicle_cache["data"] is None or
        (current_time - vehicle_cache["last_updated"]) > CACHE_TTL
    ):
        logger.info("[CACHE MISS] Reloading from API")

        response = get_vehicle_details(company_id)
        vehicle_list = response.get("VehicleList", [])

        vehicle_map = {
            str(v.get("NumberPlate")).strip(): v
            for v in vehicle_list
            if isinstance(v, dict) and v.get("NumberPlate")
        }

        vehicle_cache["data"] = vehicle_list
        vehicle_cache["vehicle_map"] = vehicle_map
        vehicle_cache["last_updated"] = current_time

        logger.info(f"[CACHE BUILT] {len(vehicle_map)} vehicles loaded")

    else:
        logger.info("[CACHE HIT] Using existing cache")

    return vehicle_cache


def get_vehicle_from_cache(vehicle_id, company_id):
    cache = load_vehicle_cache(company_id)
    return cache["vehicle_map"].get(str(vehicle_id))
