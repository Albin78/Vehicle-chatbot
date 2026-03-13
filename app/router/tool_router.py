from app.tools.db_tool import fetch_telemetry
from app.tools.analytics_tool import run_analytics
from app.tools.external_api_tool import battery_service


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
        return battery_service(plan.imei)