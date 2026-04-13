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
    # FIELD CLEANING
    # -----------------------------
    @field_validator("*", mode="before")
    @classmethod
    def clean_null_strings(cls, v):
        """
        Normalize string nulls coming from LLM:
        "null", "None", "" → None
        """
        if isinstance(v, str) and v.strip().lower() in {"null", "none", ""}:
            return None
        return v


    # -----------------------------
    # BUSINESS RULE VALIDATION
    # -----------------------------
    @model_validator(mode="after")
    def enforce_rules(self):

        # -----------------------------
        # Normalize fields first
        # -----------------------------
        metric_exists = self.metric is not None
        vehicle_exists = self.vehicle_id is not None

        # -----------------------------
        # RULE 1: Aggregation requires metric
        # -----------------------------
        if self.aggregation and not metric_exists:
            self.aggregation = None

        # -----------------------------
        # RULE 2: Service (STRICT)
        # -----------------------------
        if vehicle_exists and not metric_exists:
            self.service = "vehicle_service"
        else:
            self.service = None

        # -----------------------------
        # RULE 3: Action default
        # -----------------------------
        if self.action not in {"fetch", "update", "delete"}:
            self.action = "fetch"

        return self