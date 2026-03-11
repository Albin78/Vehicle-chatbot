from pydantic import BaseModel


class ExecutionPlan(BaseModel):

    tool: str

    operation: str

    metric: str | None

    imei: str | None

    time_range: str | None