from fastapi import HTTPException

def validate_result(result):
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No data found for this IMEI"
        )