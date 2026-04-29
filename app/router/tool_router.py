from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics
from app.tools.vehicle_resolver import resolve_vehicle
from app.tools.external_api_tool import (
    get_operation_summary,
    get_latestrecord,
    get_alertreport
)
from app.parsers.date_parser import extract_time_range
from app.validators.external_api_formatter import build_response
from app.validators.result_validator import validate_api_response
from app.utils.logger import logger


def route_tool(intent, plan, company_id):

    logger.info(f"[ROUTER] Incoming intent: {intent}")
    logger.info(f"[ROUTER] Execution plan: {plan}")

    # DB TOOL
    # --------------------------------------------------
    if plan.tool == "db":
        logger.info("[ROUTER] Routing to DB tool")
        return fetch_telemetry(plan.imei, plan.metric)

   
    # ANALYTICS TOOL
    # --------------------------------------------------
    if plan.tool == "analytics":
        logger.info("[ROUTER] Routing to Analytics tool")
        return run_analytics(
            plan.imei,
            plan.metric,
            plan.operation
        )


    # EXTERNAL API ROUTING
    # --------------------------------------------------
    if plan.tool == "external_api":

        
        # VEHICLE RESOLUTION
        # -----------------------------
        vehicle_detail = resolve_vehicle(plan.vehicle_id, company_id)
        logger.info(f"[ROUTER] Vehicle resolved: {vehicle_detail}")

        if not vehicle_detail:
            logger.error("[ROUTER] Vehicle not found")
            return {"type": "error", "message": "Vehicle not found"}

        vehicle_id = vehicle_detail["ID"]

      
        if intent.service == "alert_service":
            logger.info("[ROUTER] Routing to Alert API")

            parsed = extract_time_range(plan.time_range)
            logger.info(f"Date formatted fetched in backend: {parsed}")
            if not parsed:
                return {"type": "error", "message": "Time range required for alerts"}

            from_date, to_date = parsed

            result = get_alertreport(
                id=vehicle_id,
                company_id=company_id,
                from_date=from_date,  # type: ignore
                to_date=to_date       # type: ignore
            )
            logger.info(f"Total alerts from alert api result for the given range: {result.get('total', 0)}")

    
        elif intent.service == "realtime_service":
            logger.info("[ROUTER] Routing to Latest Record API")

            result = get_latestrecord(company_id=company_id)

       
        elif intent.service == "summary_service":
            logger.info("[ROUTER] Routing to Operation Summary API")

            parsed = extract_time_range(plan.time_range)
            logger.info(f"Date formatted fetched in backend: {parsed}")
            
            if not parsed:
                return {"type": "error", "message": "Time range required"}

            from_date, to_date = parsed

            result = get_operation_summary(
                id=vehicle_id,
                company_id=company_id,
                from_date=from_date, # type: ignore
                to_date=to_date     # type: ignore
            )

        else:
            logger.error(f"[ROUTER] Unknown service: {intent.service}")
            return {"type": "error", "message": "Invalid service type"}

        logger.info("[ROUTER] Validating API response")

        validation = validate_api_response(result)

        if validation["type"] == "error":
            logger.error(f"[ROUTER] Validation failed: {validation['message']}")
            return {
                "type": "error",
                "message": validation["message"]
            }

        validated_data = validation["data"]

        logger.info(f"[ROUTER] Validated data: {validated_data}")

        final_response = build_response(intent, validated_data)

        logger.info(f"[ROUTER] Final response: {final_response}")

        return final_response