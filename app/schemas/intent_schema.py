import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class QueryIntent(BaseModel):
    action: Optional[str] = None
    vehicle_id: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    analysis: Optional[str] = None
    time_range: Optional[str] = None
    service: Optional[str] = None


    # -----------------------------
    # CLEAN NULL STRINGS
    # -----------------------------
    @field_validator("*", mode="before")
    @classmethod
    def clean_null_strings(cls, v):
        if isinstance(v, str) and v.strip().lower() in {"null", "none", ""}:
            return None
        return v


    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    @field_validator("vehicle_id", mode="before")
    @classmethod
    def normalize_vehicle_id(cls, v):
        if isinstance(v, str):
            return re.sub(r"\s+", "", v).upper()
        return v


    @field_validator("time_range", mode="before")
    @classmethod
    def normalize_time_range(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v


    # -----------------------------
    # BUSINESS RULES (UPDATED)
    # -----------------------------
    @model_validator(mode="after")
    def enforce_rules(self):

        metric_exists = self.metric is not None
        vehicle_exists = self.vehicle_id is not None

        # Aggregation requires metric
        if self.aggregation and not metric_exists:
            self.aggregation = None

        # Action default
        if self.action not in {"fetch", "update", "delete"}:
            self.action = "fetch"

        # -----------------------------
        # SERVICE (UPDATED LOGIC)
        # -----------------------------
        if vehicle_exists:
            # ALWAYS go through vehicle_service first
            self.service = "vehicle_service"
        else:
            self.service = None

        return self