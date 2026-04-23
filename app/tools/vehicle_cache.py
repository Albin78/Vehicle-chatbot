# vehicle_cache.py
from app.tools.external_api_tool import get_vehicle_details, get_latestrecord
from app.utils.logger import logger
import time


GLOBAL_CACHE = {
    "vehicle_list": {},
    "realtime": {},
    "alerts": {},
    "summary": {}
}

CACHE_TTL = {
    "vehicle_list": 1200,   # 20 min
    "realtime": 30,         # 30 sec
    "alerts": 120,          # 2 min
    "summary": 600          # 10 min
}


def get_cached_data(cache_key, fetch_fn, ttl, key_builder=None):
    import time

    cache = GLOBAL_CACHE.get(cache_key, {})

    current_time = time.time()

    if (
        not cache or
        (current_time - cache.get("last_updated", 0)) > ttl
    ):
        logger.info(f"[CACHE MISS] {cache_key}")

        data = fetch_fn()

        index = {}
        if key_builder:
            for item in data:
                k = key_builder(item)
                if k:
                    index[k] = item

        GLOBAL_CACHE[cache_key] = {
            "data": data,
            "index": index,
            "last_updated": current_time
        }

    else:
        logger.info(f"[CACHE HIT] {cache_key}")

    return GLOBAL_CACHE[cache_key]


# vehicle_cache = {
#     "data": None,
#     "vehicle_map": {},
#     "last_updated": None
# }


# CACHE_TTL = 1200  # 5 minutes

def normalize_vehicle_id(v_id: str) -> str:
    if not v_id:
        return ""
    return "".join(v_id.split()).upper()


def vehicle_key_builder(v):
    plate = v.get("NumberPlate")
    return normalize_vehicle_id(plate) if plate else None


def get_vehicle_cache(company_id):
    return get_cached_data(
        cache_key="vehicle_list",
        fetch_fn=lambda: get_vehicle_details(company_id).get("VehicleList", []),
        ttl=CACHE_TTL["vehicle_list"],
        key_builder=vehicle_key_builder
    )


def realtime_key_builder(v):
    plate = v.get("numberPlate")
    return normalize_vehicle_id(plate) if plate else None


def get_realtime_cache(company_id):
    return get_cached_data(
        cache_key="realtime",
        fetch_fn=lambda: get_latestrecord(company_id).get("data", []),
        ttl=CACHE_TTL["realtime"],
        key_builder=realtime_key_builder
    )



# def load_vehicle_cache(company_id):
#     current_time = time.time()

#     if (
#         vehicle_cache["data"] is None or
#         (current_time - vehicle_cache["last_updated"]) > CACHE_TTL
#     ):
#         logger.info("[CACHE MISS] Reloading from API")

#         response = get_vehicle_details(company_id)
#         vehicle_list = response.get("VehicleList", [])

#         vehicle_map = {}

#         for v in vehicle_list:
#             if not isinstance(v, dict):
#                 continue

#             number_plate = v.get("NumberPlate")
            
#             # Normalize keys
#             if number_plate:
#                 norm_plate = normalize_vehicle_id(number_plate)
#                 vehicle_map[norm_plate] = v

#         vehicle_cache["data"] = vehicle_list
#         vehicle_cache["vehicle_map"] = vehicle_map
#         vehicle_cache["last_updated"] = current_time

#         logger.info(f"[CACHE BUILT] {len(vehicle_map)} indexed keys")

#     else:
#         logger.info("[CACHE HIT] Using existing cache")
    
#     logger.info(f"Vehicle map Cache: {vehicle_cache['vehicle_map']}")

#     return vehicle_cache


# def get_vehicle_from_cache(vehicle_id, company_id):
#     cache = load_vehicle_cache(company_id)
#     key = normalize_vehicle_id(vehicle_id)
#     logger.info(f"Normalized vehicle ids: {key}")
#     return cache["vehicle_map"].get(key)
