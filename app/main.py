from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import router
from app.config import get_settings


settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="IntakeTrace",
    version=__version__,
    description="Evidence-backed AI intake processing with deterministic safety gates.",
)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "The request body does not match the intake API contract.",
                "retryable": False,
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_error(_: Request, __: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("Unhandled API error")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "The service encountered an unexpected error.",
                "retryable": False,
            }
        },
    )
