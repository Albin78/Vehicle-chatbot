# vehicle_cache.py

import time
import re

from app.tools.external_api_tool import get_vehicle_details
from app.utils.logger import logger


# =========================================================
# GLOBAL CACHE
# =========================================================

GLOBAL_CACHE = {
    "vehicle_list": {},
    "alerts": {},
    "summary": {}
}


# =========================================================
# CACHE TTL
# =========================================================

CACHE_TTL = {

    # Vehicle metadata changes rarely
    "vehicle_list": 600,

    # Alerts can tolerate small delay
    "alerts": 120,

    # Summary analytics expensive
    "summary": 600
}


# =========================================================
# NORMALIZATION
# =========================================================



import re


def normalize_vehicle_id(v_id: str) -> str:

    if not v_id:
        return ""

    v_id = v_id.upper()

    parts = re.findall(
        r"[A-Z]+|\d+",
        v_id
    )

    numbers = []
    letters = []

    for part in parts:

        if part.isdigit():
            numbers.append(part)

        else:
            letters.append(part)

    return "".join(numbers) + "".join(letters)


# =========================================================
# GENERIC CACHE LOADER
# =========================================================

def get_cached_data(
    cache_key,
    fetch_fn,
    ttl,
    key_builder=None
):

    cache = GLOBAL_CACHE.get(cache_key, {})

    current_time = time.time()

    # -----------------------------------------------------
    # CACHE MISS
    # -----------------------------------------------------

    if (
        not cache or
        (current_time - cache.get("last_updated", 0)) > ttl
    ):

        logger.info(f"[CACHE MISS] {cache_key}")

        data = fetch_fn()

        index = {}

        # Optional indexing
        if key_builder:

            for item in data:

                try:

                    k = key_builder(item)

                    if k:
                        index[k] = item

                except Exception:
                    continue

        GLOBAL_CACHE[cache_key] = {
            "data": data,
            "index": index,
            "last_updated": current_time
        }

    # -----------------------------------------------------
    # CACHE HIT
    # -----------------------------------------------------

    else:

        logger.info(f"[CACHE HIT] {cache_key}")

    return GLOBAL_CACHE[cache_key]


# =========================================================
# VEHICLE CACHE INDEX BUILDER
# =========================================================

def vehicle_key_builder(vehicle):

    plate = vehicle.get("NumberPlate")

    if not plate:
        return None

    normalized = normalize_vehicle_id(plate)

    return normalized


# =========================================================
# VEHICLE CACHE
# =========================================================

def get_vehicle_cache(company_id):

    return get_cached_data(

        cache_key="vehicle_list",

        fetch_fn=lambda: (
            get_vehicle_details(company_id)
            .get("VehicleList", [])
        ),

        ttl=CACHE_TTL["vehicle_list"],

        key_builder=vehicle_key_builder
    )


# =========================================================
# GET VEHICLE FROM CACHE
# =========================================================

def get_vehicle_from_cache(
    vehicle_id,
    company_id
):

    cache = get_vehicle_cache(company_id)

    normalized_id = normalize_vehicle_id(vehicle_id)

    logger.info(
        f"Normalized Vehicle ID: {normalized_id}"
    )

    return cache["index"].get(normalized_id)