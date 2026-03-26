from fastapi import APIRouter

from app.schemas.request_schema import QueryRequest
from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.validators.result_validator import validate_result
from app.agent.response_generator import generate_response
from app.validators.intent_validation import validate_intent
from app.validators.external_api_formatter import extract_imei_from_query
from app.utils.logger import logger

router = APIRouter()


@router.post("/query")
def query_system(data: QueryRequest):

    if not data.query:
        return {
            "response": "Please provide query."
        }

    intent = extract_intent(data.query)

    logger.info(f"Intent: {intent}")

    if not validate_intent(intent):
        return {
             "response": "I am a VMS chatbot, I am unable to answer the question."
        }
    
    imei = extract_imei_from_query(data.query)

    plan = create_plan(intent, imei)

    result = route_tool(plan)
    
    logger.info(f"Final result before validation: {result}, type: {type(result)}")
    
    validate_result(result)

    response = generate_response(data.query, result, intent)
    
    logger.info(f"Response: {response}")

    return {"response": response}
