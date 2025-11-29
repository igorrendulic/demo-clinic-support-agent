from fastapi import FastAPI, HTTPException, Request
import uvicorn
from fastapi.responses import JSONResponse
import logging
import sys
from api.router import root_router
from api.chat_api import chat_router
import os
from logging_config import logger

os.environ["RUN_MODE"] = "api"

EXCEPTION_LOG_LEVELS = {
    "HTTPException": "error",
    "RequestValidationError": "warning",
    "HTTPValidationError": "warning",
    "StarletteRequestValidationError": "warning",
    "StarletteHTTPException": "error",
}

app = FastAPI(
    title="Appointment Scheduler Demo API",
    description="This is a demo API for the Appointment Scheduler platform.",
    version="1.0.0",
)

app.include_router(root_router)
app.include_router(chat_router)

@app.exception_handler(HTTPException)
async def unified_exception_handler(request: Request, exc: HTTPException):
    """Handles multiple HTTP exceptions dynamically."""
    
    log_level = EXCEPTION_LOG_LEVELS.get(exc.__class__.__name__, "error")  # Default to "error"
    
    log_message = f"{exc.__class__.__name__}: {exc.detail}"
    
    # Log at the appropriate level
    if log_level == "info":
        logger.info(log_message)
    elif log_level == "warning":
        logger.warning(log_message)
    elif log_level == "error":
        logger.error(log_message, exc_info=True)  # Logs full traceback

    sys.stdout.flush()  # Ensure logs appear immediately

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)