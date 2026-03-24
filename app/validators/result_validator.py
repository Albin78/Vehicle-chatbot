from fastapi import HTTPException

def validate_result(result):

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for this IMEI"
        )