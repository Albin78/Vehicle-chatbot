from pydantic import BaseModel


class ExecutionPlan(BaseModel):

    tool: str

    operation: str

    metric: str 

    imei: str | None

    vehicle_id: str | None

    time_range: str | None