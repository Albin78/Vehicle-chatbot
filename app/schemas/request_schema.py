from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):

    query: str
    company_id: Optional[int]

    # imei: Optional[str]