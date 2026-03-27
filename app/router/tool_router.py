from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics
from app.tools.external_api_tool import get_vehicle_details, get_vehicle_by_imei
from app.validators.external_api_formatter import data_formatter
from app.utils.logger import logger


def route_tool(plan):

    if plan.tool == "db":
        return fetch_telemetry(plan.imei, plan.metric)

    if plan.tool == "analytics":
        return run_analytics(
            plan.imei,
            plan.metric,
            plan.operation
        )

    if plan.tool == "external_api":
        data = get_vehicle_details()
        vehicle_detail = get_vehicle_by_imei(data, plan.imei)
        logger.info(f"Vehicle detail using imei {plan.imei}:{vehicle_detail}")
        return data_formatter(vehicle_detail)
