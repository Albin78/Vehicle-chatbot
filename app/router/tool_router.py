from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics
from app.tools.vehicle_cache import get_vehicle_from_cache
from app.validators.external_api_formatter import data_formatter
from app.utils.logger import logger
from app.validators.result_validator import validate_api_response


def route_tool(plan, company_id):

    if plan.tool == "db":
        return fetch_telemetry(plan.imei, plan.metric)

    if plan.tool == "analytics":
        return run_analytics(
            plan.imei,
            plan.metric,
            plan.operation
        )

    if plan.tool == "external_api":

        vehicle_detail = get_vehicle_from_cache(plan.vehicle_id, company_id)

        validation = validate_api_response(vehicle_detail)

        if validation["type"] == "error":
            return validation["message"]

        validated_result = validation["data"]

        logger.info(f"Vehicle detail using vehicle_id {plan.vehicle_id}: {validated_result}")

        return data_formatter(validated_result)
