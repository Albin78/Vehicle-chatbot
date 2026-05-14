from app.tools.vehicle_resolver import resolve_vehicle

from app.tools.external_api_tool import combined_report

from app.builders.api_payload_builder import (
    build_combined_payload
)

from app.validators.result_validator import (
    validate_api_response
)

from app.builders.response_route import (
    build_response
)

from app.utils.logger import logger


def handle_vehicle_service(
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

    logger.info(f"[SERVICE] Vehicle: {vehicle}")

    # --------------------------------------------------
    # BUILD PAYLOAD
    # --------------------------------------------------

    payload = build_combined_payload(
        intent=intent,
        plan=plan,
        vehicle=vehicle,
        company_id=company_id
    )

    logger.info(f"[SERVICE] Payload: {payload}")

    result = combined_report(**payload)

    logger.info(f"[SERVICE] API Result: {result}")

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    validation = validate_api_response(result)

    if validation["type"] == "error":

        return validation

    validated_data = validation["data"]

    # --------------------------------------------------
    # FORMAT RESPONSE
    # --------------------------------------------------

    return build_response(
        intent,
        validated_data
    )