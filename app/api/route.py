from fastapi import APIRouter
from typing import Optional

from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.validators.result_validator import validate_result
from app.agent.response_generator import generate_response

router = APIRouter()


@router.post("/query")
def query_system(query: str, imei: Optional[int] = None):

    intent = extract_intent(query)

    plan = create_plan(intent)

    result = route_tool(plan)

    validate_result(result)

    response = generate_response(query, result)

    return {"response": response}