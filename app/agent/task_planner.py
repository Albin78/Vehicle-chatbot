from app.schemas.intent_schema import QueryIntent
from app.schemas.plan_schema import ExecutionPlan
from typing import Optional


def create_plan(intent: QueryIntent, imei: Optional[str]) -> ExecutionPlan:

    if intent.service:

        return ExecutionPlan(
            tool="external_api",
            operation=intent.service,
            metric="",
            imei=imei,
            time_range=None
        )

    if intent.analysis or intent.aggregation:

        return ExecutionPlan(
            tool="analytics",
            operation=intent.analysis or intent.aggregation or "",
            metric=intent.metric or "",
            imei=imei,
            time_range=intent.time_range
        )

    return ExecutionPlan(
        tool="db",
        operation="fetch",
        metric=intent.metric or "",
        imei=imei,
        time_range=intent.time_range
    )