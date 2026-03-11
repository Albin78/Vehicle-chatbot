from app.schemas.intent_schema import QueryIntent
from app.schemas.plan_schema import ExecutionPlan


def create_plan(intent: QueryIntent) -> ExecutionPlan:

    if intent.service:

        return ExecutionPlan(
            tool="external_api",
            operation=intent.service,
            metric=None,
            imei=intent.imei,
            time_range=None
        )

    if intent.analysis or intent.aggregation:

        return ExecutionPlan(
            tool="analytics",
            operation=intent.analysis or intent.aggregation,
            metric=intent.metric,
            imei=intent.imei,
            time_range=intent.time_range
        )

    return ExecutionPlan(
        tool="telemetry",
        operation="fetch",
        metric=intent.metric,
        imei=intent.imei,
        time_range=intent.time_range
    )