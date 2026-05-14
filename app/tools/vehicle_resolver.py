from app.tools.vehicle_cache import get_vehicle_cache, normalize_vehicle_id
from app.utils.logger import logger


def resolve_vehicle(vehicle_id: str, company_id: int):
    if not vehicle_id:
        return None

    cache = get_vehicle_cache(company_id)

    if not cache or "index" not in cache:
        logger.error("[RESOLVER] Cache missing or invalid")
        return None
    
    logger.info(f"Cache builded: {cache}")
    key = normalize_vehicle_id(vehicle_id)

    vehicle = cache["index"].get(key)
    
    if not vehicle:
        logger.warning(f"[RESOLVER] Vehicle not found for ID: {vehicle_id}")
        return None
    
    logger.info(f"Vehicle cache: {vehicle}")

    return {
        "imei": vehicle.get("IMEI"),
        "ID": vehicle.get("ID"),
        "vehicle_id": vehicle.get("NumberPlate")
    }