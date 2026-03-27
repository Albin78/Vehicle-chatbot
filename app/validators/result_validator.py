from fastapi import HTTPException
from typing import  Any

def validate_result(result):

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for this IMEI"
        )
    

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