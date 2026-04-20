from typing import  Any
from app.utils.logger import logger
from typing_extensions import Any

def validate_result(result):

    if result is None:

        logger.info("Inside the validate result function")
        return {
            "type": "error",
            "message": "Result not found for this IMEI. The data for this IMEI does not exist in the database. Please check if IMEI provided is valid or IMEI is missing in query."
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
    

def validate_intent(intent):

    is_telemetry = intent.metric is not None
    is_vehicle = intent.service == "vehicle_service"
    have_timerange = intent.time_range is not None

    if intent.action == "fetch" and not (is_telemetry or is_vehicle):
        return {
            "type": "error",
            "message": "I am VMS Chatbot. I can't answer to these questions."
        }
    
    elif not have_timerange:
        return {
            "type": "error",
            "message": "Time range is missing in the query. Check if you have passed time range."
        }

    return {
        "type": "success",
        "message": None
    }

