from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):

    query: str
    session_id: Optional[str] = None
    # company_id: Optional[int]

    # imei: Optional[str]