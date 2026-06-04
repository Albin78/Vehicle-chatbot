from pydantic import BaseModel
from typing import Optional


class ExecutionPlan(BaseModel):

    tool: str

    operation: Optional[str] = None

    metrics: list[str] = []

    aggregation: Optional[str] = None

    alert_analysis: Optional[str] = None

    imei: Optional[str] = None

    vehicle_id: Optional[str] = None

    time_range: Optional[tuple[str, str]] = None

    fleet_scope: bool = False   # True = fleet-wide, no vid required