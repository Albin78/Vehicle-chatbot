import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator



def _normalize_keywords(v: str) -> str:
    v = v.lower()

    # normalize variants
    v = re.sub(r"\bin\s+between\b", "between", v)
    v = re.sub(r"\bbetween\s+in\b", "between", v)

    # normalize connectors
    v = re.sub(r"\btill\b|\buntil\b|\bthrough\b", "to", v)

    # normalize hyphen
    v = re.sub(r"\s*-\s*", " to ", v)

    # normalize "between X and Y" → "X to Y"
    v = re.sub(r"between\s+(.+?)\s+and\s+(.+)", r"\1 to \2", v)

    # normalize "from X to Y" → "X to Y"
    v = re.sub(r"from\s+(.+?)\s+to\s+(.+)", r"\1 to \2", v)

    return v


# def _extract_date_range(v: str) -> str | None:
#     """
#     Extract structured date range into canonical format.
#     """

#     # Pattern 1: april 1 to 10
#     m = re.search(r"([a-z]+\s+\d{1,2})\s+to\s+(\d{1,2})", v)
#     if m:
#         return f"{m.group(1)} to {m.group(2)}"

#     # Pattern 2: 1 april to 10 april
#     m = re.search(r"(\d{1,2}\s+[a-z]+)\s+to\s+(\d{1,2}\s+[a-z]+)", v)
#     if m:
#         return f"{m.group(1)} to {m.group(2)}"

#     return None


class QueryIntent(BaseModel):
    action: Optional[str] = None
    vehicle_id: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    analysis: Optional[str] = None
    time_range: Optional[tuple[str, str]] = None
    service: Optional[str] = None
    intent_type: Optional[str]


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
    # VEHICLE ID VALIDATION (STRICT)
    # -----------------------------
    @field_validator("vehicle_id", mode="before")
    @classmethod
    def normalize_vehicle_id(cls, v):
        if isinstance(v, str):
            return re.sub(r"\s+", "", v).upper()
        return v


    # -----------------------------
    # METRIC NORMALIZATION
    # -----------------------------
    @field_validator("metric", mode="before")
    @classmethod
    def normalize_metric(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v


    # -----------------------------
    # TIME RANGE NORMALIZATION
    # -----------------------------
    @field_validator("time_range", mode="before")
    @classmethod
    def normalize_time_range(cls, v):
        if not isinstance(v, str):
            return v

        v = v.strip().lower()

        # Step 1: normalize noisy language
        v = _normalize_keywords(v)

        return v

        # # Step 2: extract structured range
        # parsed = _extract_date_range(v)

        # return parsed


    # -----------------------------
    # BUSINESS RULES
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

        return self