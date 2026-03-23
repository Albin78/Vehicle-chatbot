from fastapi import APIRouter

from app.schemas.request_schema import QueryRequest
from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.validators.result_validator import validate_result
from app.agent.response_generator import generate_response
from app.validators.intent_validation import validate_intent
from app.utils.logger import logger

router = APIRouter()


@router.post("/query")
def query_system(data: QueryRequest):

    intent = extract_intent(data.query)

    if not validate_intent(intent):
        return {
             "response": "I am a VMS chatbot, I am unable to answer the question."
        }

    plan = create_plan(intent, data.imei)

    result = route_tool(plan)
    
    logger.info(f"Result: {result}")
    
    validate_result(result)

    response = generate_response(data.query, result)
    
    logger.info(f"Response: {response}")

    return {"response": response}
