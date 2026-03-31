from fastapi import APIRouter

from app.schemas.request_schema import QueryRequest
from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.tools.external_api_tool import get_vehicle_by_imei
from app.validators.result_validator import validate_result, validate_intent, validate_action
from app.agent.response_generator import generate_response
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
    logger.info(f"Intent action fetching: {intent.action}")

    intent_validation = validate_intent(intent)

    if intent_validation["type"] == "error":
        return intent_validation["message"]
    
    action_validation = validate_action(intent)
    
    if action_validation["type"] == "error":
        return action_validation["message"]

    imei = extract_imei_from_query(data.query)

    plan = create_plan(intent, imei)

    result = route_tool(plan)
    
    logger.info(f"Final result before validation: {result}, type: {type(result)}")
    
    validation = validate_result(result)
    if validation["type"] == "error":
        return validation["message"]
    
    validated_result = validation["data"]

    response = generate_response(data.query, validated_result, intent)
    
    logger.info(f"Response: {response}")

    return {"response": response}
