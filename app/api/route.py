from fastapi import APIRouter

from app.schemas.request_schema import QueryRequest
from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.validators.result_validator import validate_result, validate_intent, validate_action
from app.agent.response_generator import generate_response
from app.utils.logger import logger
from app.tools.vehicle_resolver import resolve_vehicle

router = APIRouter()


@router.post("/query")
def query_system(data: QueryRequest):

    if not data.query:
        return {"response": "Please provide query."}
    
    company_id = data.company_id

    if not company_id:
        return {"response": "Please provide company id."}
    
    
    logger.info(f"Passed query: {data.query}")

    intent = extract_intent(data.query)
        
    logger.info(f"Intent: {intent}")
    logger.info(f"Intent vehicle id: {intent.vehicle_id}")

    if not intent.vehicle_id:
        return {"response": "Please provide a vehicle ID to proceed."}  

    intent_validation = validate_intent(intent)
    if intent_validation["type"] == "error":
        return {"response": intent_validation["message"]}

    action_validation = validate_action(intent)
    if action_validation["type"] == "error":
        return {"response": action_validation["message"]}

    # NEW: RESOLVE VEHICLE
    # -----------------------------
    vehicle_context = None

    if intent.vehicle_id:
        vehicle_context = resolve_vehicle(intent.vehicle_id, company_id)

        if not vehicle_context:
            return {"response": "Vehicle not found."}

    imei = vehicle_context["imei"] if vehicle_context else None
    vehicle_id = vehicle_context["vehicle_id"] if vehicle_context else None

    # PLAN
    # -----------------------------
    plan = create_plan(intent, imei=imei, vehicle_id=vehicle_id)

    # EXECUTION
    # -----------------------------
    result = route_tool(intent, plan, company_id)

    logger.info(f"Final result before validation: {result}, type: {type(result)}")

    validation = validate_result(result)
    if validation["type"] == "error":
        return {"response": validation["message"]}

    validated_result = validation["data"]

    response = generate_response(validated_result, intent)

    logger.info(f"Response: {response}")

    return {"response": response}
