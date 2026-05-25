import re

from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import field_validator
from pydantic import model_validator


class QueryIntent(BaseModel):

    action: Literal[
        "fetch",
        "update",
        "delete"
    ] = "fetch"

    vehicle_id: Optional[str] = None

    source: Optional[
        Literal[
            "latest",
            "summary",
            "alert"
        ]
    ] = None

    metrics: list[str] = []

    aggregation: Optional[
        Literal[
            "minimum",
            "maximum",
            "average"
        ]
    ] = None

    # ---------------------------------
    # ALERT ANALYSIS
    # ---------------------------------
    alert_analysis: Optional[
        Literal[
            "latest",
            "count",
            "summary"
        ]
    ] = None

    time_range: Optional[tuple[str, str]] = None
    
    alert_focus: Optional[str] = ""

    alert_response_type: str = ""
    
    summary_requested: bool = False

    # ---------------------------------
    # ALERT ENABLE / DISABLE CHECK
    # ---------------------------------
    alert_enable_check: bool = False

    alert_type_focus: Optional[str] = None

    alert_time_range_default: bool = False 



    # ==========================================
    # CLEAN NULL STRINGS
    # ==========================================
    @field_validator("*", mode="before")
    @classmethod
    def clean_null_strings(cls, v):

        if isinstance(v, str):

            if v.strip().lower() in {
                "null",
                "none",
                ""
            }:
                return None

        return v

    # ==========================================
    # VEHICLE NORMALIZATION
    # ==========================================
    @field_validator("vehicle_id", mode="before")
    @classmethod
    def normalize_vehicle_id(cls, v):

        if isinstance(v, str):

            return re.sub(
                r"\s+",
                "",
                v
            ).upper()

        return v

    # ==========================================
    # METRIC NORMALIZATION
    # ==========================================
    @field_validator("metrics", mode="before")
    @classmethod
    def normalize_metrics(cls, v):

        if v is None:
            return []

        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            return []

        normalized = []

        for metric in v:

            if isinstance(metric, str):

                metric = (
                    metric
                    .strip()
                    .lower()
                )

                if metric:
                    normalized.append(metric)

        return list(set(normalized))

    # ==========================================
    # BUSINESS RULES
    # ==========================================
    @model_validator(mode="after")
    def validate_business_rules(self):

        # Aggregation requires metrics
        if self.aggregation and not self.metrics:
            self.aggregation = None

        # Alert analysis only for alerts
        if self.source != "alert":
            self.alert_analysis = None

        # summary_requested only for latest
        if self.source != "latest":
            self.summary_requested = False

        # alert_enable_check and alert_type_focus only for alert_enable
        if self.source != "alert_enable":
            self.alert_enable_check = False
            self.alert_type_focus = None

        return self