from typing import  Any
from app.utils.logger import logger
from typing import Any


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
    


def validate_api_response(
    api_response: dict[str, Any] | None
) -> dict[str, Any]:

    logger.info("[VALIDATOR] Validating API response")

    # -------------------------------------------------
    # NULL RESPONSE
    # -------------------------------------------------

    if api_response is None:

        return {
            "type": "error",
            "message": "API returned no response"
        }

    # -------------------------------------------------
    # INVALID TYPE
    # -------------------------------------------------

    if not isinstance(api_response, dict):

        return {
            "type": "error",
            "message": "Invalid API response structure"
        }

    # -------------------------------------------------
    # EMPTY RESPONSE
    # -------------------------------------------------

    if not api_response:

        return {
            "type": "error",
            "message": "No vehicle data found"
        }

    # -------------------------------------------------
    # API FAILURE
    # -------------------------------------------------

    if api_response.get("status") == "failed":

        return {
            "type": "error",
            "message": api_response.get(
                "message",
                "External API failed"
            )
        }

    # -------------------------------------------------
    # SUCCESS
    # -------------------------------------------------

    return {
        "type": "success",
        "data": api_response
    }


def validate_action(intent) -> dict[str, Any]:

    
    # VALID ACTION
    # -----------------------------------------

    if intent.action != "fetch":

        return {
            "type": "error",
            "message": "Unsupported action"
        }
    
    return {
        "type": "success",
        "message": None
    }
    

def validate_intent(intent):

    valid_sources = {
        "latest",
        "summary",
        "alert",
        "alert_enable",
        "fleet_analytics"
    }

    if intent.source not in valid_sources:

        return {
            "type": "error",
            "message": "Invalid source detected"
        }

    if not intent.vehicle_id and intent.source != "fleet_analytics":

        return {
            "type": "error",
            "message": "Vehicle ID missing"
        }


    if intent.source == "summary":

        if not intent.time_range:

            return {
                "type": "error",
                "message": "Time range required for summary queries"
            }


    if intent.source == "alert":

        if not intent.time_range:

            return {
                "type": "error",
                "message": "Time range required for alert queries"
            }


    if intent.source == "latest":


        if intent.aggregation:

            return {
                "type": "error",
                "message": "Aggregation not allowed for realtime queries"
            }

    return {
        "type": "success",
        "message": None
    }
