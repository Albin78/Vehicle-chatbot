from typing import  Any
from app.utils.logger import logger
from typing_extensions import Any

def validate_result(result):

    if not result:

        logger.info("Inside the validate result function")
        return {
            "type": "error",
            "message": "Result not found for this IMEI"
        }
    return {
        "type": "Result data",
        "data": result
    }
    

def validate_api_response(api_response: dict[str, Any] | None) -> dict[str, Any]:
    if not api_response:
        return {
            "type": "error",
            "message": "Invalid IMEI for this company"
        }
    return {
        "type": "vehicle_data",
        "data": api_response
    }


def validate_action(intent) -> dict[str, Any]:
    if intent.action != "fetch":
        logger.info("Inside the validate action function")
        return {
            "type": "error",
            "message": "This action is not permitted"
        }
    
    return {
        "type": "success",
        "message": None
    }
    

def validate_intent(intent) -> dict[str, Any]:

    if not any([
        intent.metric,
        intent.aggregation,
        intent.analysis,
        intent.service,
    ]) and intent.action == 'fetch':
        
        logger.info("Inside validate intent function")
        return {
            "type": "error",
            "message": "I am VMS Chatbot. I can't answer to these questions."
        }

    return {
        "type": "success",
        "message": None
    }

