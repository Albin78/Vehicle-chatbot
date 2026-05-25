from app.tools.vehicle_resolver import resolve_vehicle
from app.tools.external_api_tool import get_alert_enable_status
from app.builders.alert_enable_builder import build_alert_enable_response
from app.utils.logger import logger


def handle_alert_enable_service(
    intent,
    plan,
    company_id
):

    # --------------------------------------------------
    # RESOLVE VEHICLE
    # --------------------------------------------------

    vehicle = resolve_vehicle(
        plan.vehicle_id,
        company_id
    )

    if not vehicle:

        return {
            "type": "error",
            "message": "Vehicle not found"
        }

    logger.info(f"[ALERT ENABLE SERVICE] Vehicle: {vehicle}")

    vehicle_numeric_id = vehicle.get("ID")

    # --------------------------------------------------
    # CALL ALERT ENABLE API
    # --------------------------------------------------

    api_result = get_alert_enable_status(
        company_id=company_id
    )

    if not isinstance(api_result, dict) or api_result.get("response"):

        return {
            "type": "error",
            "message": api_result.get(
                "response",
                "Unable to fetch alert enable status"
            )
        }

    logger.info(f"[ALERT ENABLE SERVICE] API status: {api_result.get('status')}")

    # --------------------------------------------------
    # FIND MATCHING VEHICLE RECORD
    # --------------------------------------------------

    data_list = api_result.get("data", [])

    matched_record = None

    for record in data_list:

        record_id = record.get("ID")

        if record_id and str(record_id) == str(vehicle_numeric_id):
            matched_record = record
            break

    if not matched_record:

        logger.warning(
            f"[ALERT ENABLE SERVICE] "
            f"No alert enable record found for vehicle ID {vehicle_numeric_id}"
        )

        return {
            "type": "error",
            "message": (
                f"No alert configuration found "
                f"for vehicle {intent.vehicle_id}"
            )
        }

    logger.info(f"[ALERT ENABLE SERVICE] Matched record: {matched_record}")

    # --------------------------------------------------
    # BUILD RESPONSE
    # --------------------------------------------------

    return build_alert_enable_response(
        intent=intent,
        record=matched_record
    )
