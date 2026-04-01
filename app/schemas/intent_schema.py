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
        """
        Final deterministic layer.
        This OVERRIDES incorrect LLM output.
        """

        # -------------------------
        # RULE 1: If metric exists → NO service
        # -------------------------
        if self.metric is not None:
            self.service = None

        # -------------------------
        # RULE 2: If aggregation exists → metric must exist
        # -------------------------
        if self.aggregation is not None and self.metric is None:
            self.aggregation = None

        # -------------------------
        # RULE 3: If aggregation exists → NO service
        # -------------------------
        if self.aggregation is not None:
            self.service = None

        # -------------------------
        # RULE 4: Service allowed ONLY when safe
        # -------------------------
        if self.service is not None:
            if self.metric is not None or self.aggregation is not None:
                self.service = None  # force remove

        # -------------------------
        # RULE 5: IMEI validation
        # -------------------------
        # if self.imei is not None:
        #     if not (self.imei.isdigit() and len(self.imei) == 15):
        #         self.imei = None
        #         self.metric = None
        #         self.aggregation = None
        #         self.service = None

        return self