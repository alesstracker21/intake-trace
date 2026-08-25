from __future__ import annotations

from functools import lru_cache

from app.agents.factory import create_extraction_agent, create_review_agent
from app.config import get_settings
from app.services.extraction import ExtractionService
from app.services.pipeline import PipelineService
from app.services.review import SafetyReviewService


@lru_cache(maxsize=1)
def get_pipeline() -> PipelineService:
    settings = get_settings()
    return PipelineService(
        ExtractionService(create_extraction_agent(settings)),
        SafetyReviewService(create_review_agent(settings)),
    )
