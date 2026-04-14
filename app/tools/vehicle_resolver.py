from app.tools.vehicle_cache import get_vehicle_from_cache
from app.utils.logger import logger


def resolve_vehicle(vehicle_id: str, company_id: int):
    """
    Converts vehicle_id → full vehicle object
    """

    if not vehicle_id:
        return None

    vehicle = get_vehicle_from_cache(vehicle_id, company_id)

    if not vehicle:
        logger.warning(f"Vehicle not found for ID: {vehicle_id}")
        return None

    return {
        "imei": vehicle.get("IMEI"),
        "ID": vehicle.get("ID"),
        "vehicle_id": vehicle.get("NumberPlate")
    }