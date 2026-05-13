from app.utils.logger import logger


def error_response(message: str):

    logger.error(message)

    return {
        "type": "error",
        "message": message
    }


def success_response(response_type: str, data: dict):

    return {
        "type": response_type,
        "data": data
    }