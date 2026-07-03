import os
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import requests

from app.api.route import router
from app.utils.logger import logger
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload the Ollama model
    logger.info("Starting up: preloading model...")
    try:
        # Dummy request to wake up/load the model in Ollama
        requests.post(
            f"{settings.OLLAMA_URL}",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": "ping",
                "stream": False
            },
            timeout=5
        )
        logger.info("Model preloaded successfully.")
    except Exception as e:
        logger.warning(f"Could not preload model: {e}")
        
    yield
    # Shutdown
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

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