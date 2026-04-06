from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

class QueryIntent(BaseModel):
    metric: Optional[str] = "fetch"
    imei: Optional[str] 
    aggregation: Optional[str] 
    analysis: Optional[str]
    time_range: Optional[str] 
    service: Optional[str]
    action: Optional[str]


    @field_validator("*", mode="before")
    @classmethod
    def clean_null_strings(cls, v):
        if isinstance(v, str) and v.lower() in ["null", "none", ""]:
            return None
        return v
    
    
    @model_validator(mode="after")
    def enforce_rules(self):

        # FORCE: if metric word exists in query → kill service
        if self.metric is not None:
            self.service = None

        # CRITICAL FIX:
        if self.metric is None and self.aggregation is not None:
            # aggregation without metric → invalid → kill service
            self.service = None

        # NEW RULE (IMPORTANT):
        # If query contains metric keyword but model missed it
        # → force remove service
        # Only remove service if telemetry clearly exists
        if self.metric is not None or self.aggregation is not None:
            self.service = None

        if self.aggregation is not None and self.metric is None:
            self.aggregation = None

        return self