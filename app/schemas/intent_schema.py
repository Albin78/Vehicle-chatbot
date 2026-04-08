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
        """
        Enforce strict business logic after extraction.
        """

        # ----------------------------------
        # RULE 1: Aggregation requires metric
        # ----------------------------------
        if self.aggregation and not self.metric:
            self.aggregation = None

        # ----------------------------------
        # RULE 2: Service assignment
        # ----------------------------------
        # Service should ONLY exist for pure vehicle queries
        if self.vehicle_id and not self.metric:
            self.service = "vehicle_service"
        else:
            self.service = None

        # ----------------------------------
        # RULE 3: Action default safety
        # ----------------------------------
        if self.action not in {"fetch", "update", "delete"}:
            self.action = "fetch"

        return self