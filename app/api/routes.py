from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import __version__
from app.api.dependencies import get_pipeline
from app.config import Settings, get_settings
from app.models import ExecutionEnvelope, HealthResponse, IntakeRequest
from app.services.pipeline import PipelineService


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["operations"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="intake-trace",
        version=__version__,
        model=settings.gemini_model,
    )


@router.post(
    "/v1/intakes",
    response_model=ExecutionEnvelope,
    responses={400: {"model": ExecutionEnvelope}, 500: {"model": ExecutionEnvelope}, 502: {"model": ExecutionEnvelope}},
    tags=["intakes"],
)
async def process_intake(
    request: IntakeRequest,
    pipeline: PipelineService = Depends(get_pipeline),
):
    result = await pipeline.process(request)
    if result.processing_status == "COMPLETED":
        return result
    error = result.errors[0]
    status_code = 400 if error.code == "INVALID_INPUT" else 502 if error.retryable else 500
    return JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
