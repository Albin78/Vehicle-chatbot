from fastapi import HTTPException

def validate_result(result):

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for this IMEI"
        )
    

def validate_aapi_response(api_response):
    if not api_response:
        return "This imei not seems under the given company id"
