from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics
from app.tools.vehicle_resolver import resolve_vehicle
from app.tools.external_api_tool import get_operation_summary
from app.utils.dateparser import parse_time_range
from app.validators.external_api_formatter import build_response
from app.utils.logger import logger
from app.validators.result_validator import validate_api_response


def route_tool(intent, plan, company_id):

    if plan.tool == "db":
        return fetch_telemetry(plan.imei, plan.metric)

    if plan.tool == "analytics":
        return run_analytics(
            plan.imei,
            plan.metric,
            plan.operation
        )

    if plan.tool == "external_api":

        vehicle_detail = resolve_vehicle(plan.vehicle_id, company_id)
        logger.info(f"Vehicle details fetched: {vehicle_detail}")
        logger.info(f"Date from intent: {plan.time_range}")

        from_date, to_date = parse_time_range(plan.time_range)

        if not vehicle_detail:
            return {"response": "Vehicle not found. Check if you passed the vehicle id or not."}

        # Safe after this point
        id = vehicle_detail["ID"]
        logger.info(f"ID retrieved: {id}")
        logger.info(f"Date retrived and formatted as (start, end): {from_date, to_date}")
        
        result = get_operation_summary(
            id=id, 
            company_id=company_id,
            from_date=from_date, # type: ignore
            to_date=to_date      # type: ignore
        )

        validation = validate_api_response(result)

        if validation["type"] == "error":
            return {
                "type": "error",
                "message": validation["message"]
            }

        validated_result = validation["data"]

        logger.info(f"Vehicle detail using vehicle_id {plan.vehicle_id}: {validated_result}")

        return build_response(intent, validated_result)
