import re
from fastapi import APIRouter
from time import time

from app.schemas.request_schema import QueryRequest
from app.agent.intent_extractor import extract_intent
from app.agent.task_planner import create_plan
from app.router.tool_router import route_tool
from app.validators.result_validator import validate_result, validate_intent, validate_action
from app.agent.response_generator import generate_response
from app.utils.logger import logger
from app.tools.vehicle_resolver import resolve_vehicle
from app.memory.session_manager import session_manager
from app.agent.query_rewriter import rewrite_query

router = APIRouter()


@router.post("/query")
def query_system(data: QueryRequest):

    start_time = time()

    if not data.query:
        return {"response": "Please provide query."}
    
    company_id = 16

    # if not company_id:
    #     return {"response": "Please provide company id."}
    
    
    logger.info(f"Passed query: {data.query}")

    try:
        # Retrieve history and rewrite query
        history = session_manager.get_history(data.session_id)
        last_intent = session_manager.get_last_intent(data.session_id) if data.session_id else {}
        rewritten_query = rewrite_query(data.query, history, last_intent) if data.session_id else data.query

        intent = extract_intent(rewritten_query)

        if isinstance(intent, dict) and intent.get("error"):
            return {
                "response": intent["error"]
            }

        logger.info(f"Intent: {intent}")
        logger.info(f"Intent vehicle id: {intent.vehicle_id}")

        def is_general_query(q_str: str) -> bool:
            q = q_str.lower().strip()
            greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy", "hola"}
            if q in greetings or any(q.startswith(g + " ") for g in greetings):
                return True
            bot_info = {"who are you", "what is your name", "what can you do", "help", "how are you", "what is this"}
            if any(info in q for info in bot_info):
                return True
            has_vehicle_pattern = bool(re.search(r"\d", q))
            in_domain_keywords = [
                "vehicle", "truck", "car", "bus", "tanker", "can", "fleet", 
                "alert", "overspeed", "violation", "summary", "report", 
                "fuel", "speed", "mileage", "distance", "battery", "ignition", "engine", 
                "location", "latitude", "longitude", "odometer", "weight", "gsm", "signal", 
                "wasl", "seatbelt", "door", "camera", "immobiliz", "driver", "group", 
                "network", "satellite", "model", "make", "manufacturer", "imei"
            ]
            has_in_domain_kw = any(kw in q for kw in in_domain_keywords)
            if not has_vehicle_pattern and not has_in_domain_kw:
                return True
            general_question_starts = ["who is", "who was", "what is a", "what are", "tell me about", "how to build", "how do i"]
            if any(q.startswith(start) for start in general_question_starts) and not has_in_domain_kw:
                return True
            return False

        # Implicit Intent Inheritance
        if not intent.vehicle_id and getattr(intent, "source", None) != "fleet_analytics" and data.session_id:
            last_intent = session_manager.get_last_intent(data.session_id)
            if last_intent.get("last_vehicle_id"):
                intent.vehicle_id = last_intent["last_vehicle_id"]
                logger.info(f"Inherited vehicle_id from session: {intent.vehicle_id}")

        if not intent.vehicle_id and getattr(intent, "source", None) != "fleet_analytics":
            if is_general_query(rewritten_query):
                return {
                    "response": "I am a VMS chatbot. I am only able to answer vehicle-related queries. I can help you check vehicle status, track telemetry metrics, summarize reports, or view alerts for your fleet."
                }
            return {"response": "Please provide a valid vehicle ID to proceed."}  

        intent_validation = validate_intent(intent)
        if intent_validation["type"] == "error":
            return {"response": intent_validation["message"]}

        action_validation = validate_action(intent)
        if action_validation["type"] == "error":
            return {"response": action_validation["message"]}

        # NEW: RESOLVE VEHICLE
        # -----------------------------
        vehicle_context = None

        if intent.vehicle_id and intent.source != "fleet_analytics":
            vehicle_context = resolve_vehicle(intent.vehicle_id, company_id)

            if not vehicle_context and data.session_id:
                # LLM might have hallucinated. Try falling back to session history.
                last_intent = session_manager.get_last_intent(data.session_id)
                if last_intent.get("last_vehicle_id"):
                    logger.info(f"Vehicle {intent.vehicle_id} not found, falling back to session vehicle: {last_intent['last_vehicle_id']}")
                    intent.vehicle_id = last_intent["last_vehicle_id"]
                    vehicle_context = resolve_vehicle(intent.vehicle_id, company_id)

            if not vehicle_context:
                return {"response": f"Vehicle not found for vehicle id {intent.vehicle_id}. Check the vehicle id or try other vehicle id"}

        imei = vehicle_context["imei"] if vehicle_context else None
        vehicle_id = vehicle_context["vehicle_id"] if vehicle_context else None

        # PLAN
        # -----------------------------
        plan = create_plan(intent, imei=imei, vehicle_id=vehicle_id)

        # EXECUTION
        # -----------------------------
        result = route_tool(intent, plan, company_id)

        logger.debug(f"Final result before validation: {result}, type: {type(result)}")

        validation = validate_result(result)
        if validation["type"] == "error":
            return {"response": validation["message"]}

        validated_result = validation["data"]

        response = generate_response(validated_result, intent)

        logger.info(f"Response: {response}")

        # Save interaction to session memory
        if data.session_id:
            session_manager.add_interaction(data.session_id, rewritten_query, response, intent, validated_result)

        end_time = time()
        logger.info(f"Response after the LLM processing: {response}")
        logger.info(f"Total time taken: {end_time - start_time} seconds")

        return {"response": response}

    except Exception as e:
        logger.error(f"[GLOBAL API ERROR] {e}", exc_info=True)
        return {
            "response": "I apologize, but I encountered an issue retrieving that information right now. Please verify the vehicle ID and try again shortly."
        }
