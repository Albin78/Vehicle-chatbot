from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request

from fastapi.responses import JSONResponse

from fastapi.exceptions import (
    RequestValidationError
)

from app.api.route import router
from app.utils.logger import logger


app = FastAPI()

app.include_router(router)


# =====================================================
# HTTP EXCEPTIONS
# =====================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):

    logger.error(
        f"HTTP exception: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": (
                "Request could not be processed."
            )
        }
    )


# =====================================================
# VALIDATION EXCEPTIONS
# =====================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):

    logger.error(
        f"Validation error: {str(exc)}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": (
                "Invalid request received."
            )
        }
    )


# =====================================================
# GLOBAL EXCEPTIONS
# =====================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": (
                "Something went wrong while "
                "processing the request."
            )
        }
    )