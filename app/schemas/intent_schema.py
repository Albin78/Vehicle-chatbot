from pydantic import BaseModel
from typing import Optional


class QueryIntent(BaseModel):

    metric: Optional[str]

    imei: Optional[str]

    aggregation: Optional[str]

    analysis: Optional[str]

    time_range: Optional[str]

    service: Optional[str]