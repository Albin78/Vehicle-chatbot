from typing import Optional
from pydantic import BaseModel

class QueryIntent(BaseModel):
    metric: Optional[str] 
    aggregation: Optional[str] 
    analysis: Optional[str]
    time_range: Optional[str] 
    service: Optional[str]
    action: Optional[str]