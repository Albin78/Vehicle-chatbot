from pydantic import BaseModel
from typing_extensions import Optional

class ExecutionPlan(BaseModel):

    tool: str

    operation: str

    metric: str 

    imei: str | None

    vehicle_id: str | None

    time_range: Optional[tuple[str, str]]