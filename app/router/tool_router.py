from app.services.vehicle_combined_service import (
    handle_vehicle_service
)

from app.services.alert_enable_service import (
    handle_alert_enable_service
)

from app.services.fleet_service import (
    handle_fleet_service
)

from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics

from app.utils.logger import logger


def route_tool(intent, plan, company_id):

    logger.info(f"[ROUTER] Intent: {intent}")
    logger.info(f"[ROUTER] Plan: {plan}")

    # --------------------------------------------------
    # DB TOOL
    # --------------------------------------------------

    if plan.tool == "db":

        return fetch_telemetry(
            plan.imei,
            plan.metric
        )

    # --------------------------------------------------
    # ANALYTICS TOOL
    # --------------------------------------------------

    if plan.tool == "analytics":

        return run_analytics(
            plan.imei,
            plan.metric,
            plan.operation
        )

    # --------------------------------------------------
    # EXTERNAL API TOOL
    # --------------------------------------------------

    if plan.tool == "external_api":

        if intent.source == "alert_enable":
            return handle_alert_enable_service(
                intent=intent,
                plan=plan,
                company_id=company_id
            )

        if intent.source == "fleet_analytics":
            return handle_fleet_service(
                intent=intent,
                plan=plan,
                company_id=company_id
            )

        return handle_vehicle_service(
            intent=intent,
            plan=plan,
            company_id=company_id
        )

    return {
        "type": "error",
        "message": "Invalid tool"
    }