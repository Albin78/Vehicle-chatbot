from typing import Optional
from pydantic import BaseModel

class QueryIntent(BaseModel):
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    analysis: Optional[str] = None
    time_range: Optional[str] = None
    service: Optional[str] = None