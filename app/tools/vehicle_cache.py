# vehicle_cache.py
from app.tools.external_api_tool import get_vehicle_details
from app.utils.logger import logger
import time


vehicle_cache = {
    "data": None,
    "vehicle_map": {},
    "last_updated": None
}


CACHE_TTL = 600  # 5 minutes

def normalize_vehicle_id(v_id: str) -> str:
    if not v_id:
        return ""
    return "".join(v_id.split()).upper()



def load_vehicle_cache(company_id):
    current_time = time.time()

    if (
        vehicle_cache["data"] is None or
        (current_time - vehicle_cache["last_updated"]) > CACHE_TTL
    ):
        logger.info("[CACHE MISS] Reloading from API")

        response = get_vehicle_details(company_id)
        vehicle_list = response.get("VehicleList", [])

        vehicle_map = {}

        for v in vehicle_list:
            if not isinstance(v, dict):
                continue

            number_plate = v.get("NumberPlate")
            
            # Normalize keys
            if number_plate:
                norm_plate = normalize_vehicle_id(number_plate)
                vehicle_map[norm_plate] = v

        vehicle_cache["data"] = vehicle_list
        vehicle_cache["vehicle_map"] = vehicle_map
        vehicle_cache["last_updated"] = current_time

        logger.info(f"[CACHE BUILT] {len(vehicle_map)} indexed keys")

    else:
        logger.info("[CACHE HIT] Using existing cache")
    
    logger.info(f"Vehicle map Cache: {vehicle_cache['vehicle_map']}")

    return vehicle_cache


def get_vehicle_from_cache(vehicle_id, company_id):
    cache = load_vehicle_cache(company_id)
    key = normalize_vehicle_id(vehicle_id)
    return cache["vehicle_map"].get(key)
