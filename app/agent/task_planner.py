from typing import Optional

from app.schemas.intent_schema import QueryIntent
from app.schemas.plan_schema import ExecutionPlan


def create_plan(
    intent: QueryIntent,
    imei: Optional[str],
    vehicle_id: Optional[str]
) -> ExecutionPlan:


    if intent.source in {
        "latest",
        "summary",
        "alert",
        "alert_enable"
    }:

        return ExecutionPlan(

            tool="external_api",

            # latest / summary / alert
            operation=intent.source,

            metrics=intent.metrics,

            aggregation=intent.aggregation,

            alert_analysis=intent.alert_analysis,

            imei=imei,

            vehicle_id=vehicle_id,

            time_range=intent.time_range
        )


    if intent.aggregation:

        return ExecutionPlan(

            tool="analytics",

            operation=intent.aggregation,

            metrics=intent.metrics,

            imei=imei,

            vehicle_id=vehicle_id,

            time_range=intent.time_range
        )


    return ExecutionPlan(

        tool="db",

        operation="fetch",

        metrics=intent.metrics,

        imei=imei,

        vehicle_id=vehicle_id,

        time_range=intent.time_range
    )