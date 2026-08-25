from __future__ import annotations

import asyncio
from pathlib import Path

from app.cli import sample_requests
from app.models import AdversarialReview, IntakeProposal
from app.services.pipeline import PipelineService
from app.services.review import apply_review_policy


class FixtureExtraction:
    def __init__(self, proposal_json):
        self._proposal_json = proposal_json

    async def propose(self, intake, trace_id):
        number = int(intake.intake_id[-1])
        return IntakeProposal.model_validate(self._proposal_json(number)), 1


class PassingReview:
    async def review(self, intake, proposal, validation, trace_id):
        review = AdversarialReview(
            verdict="PASS",
            prompt_injection_detected=False,
            extraction_grounded=True,
            findings=[],
            recommended_action="Proceed with deterministic routing.",
        )
        return apply_review_policy(intake.source_text, review, validation), 1


class FailingExtraction:
    async def propose(self, intake, trace_id):
        raise TimeoutError("secret upstream details must not escape")


def test_pipeline_completes_incomplete_referral_safely(proposal_json):
    pipeline = PipelineService(FixtureExtraction(proposal_json), PassingReview())

    result = asyncio.run(pipeline.process(sample_requests()[2]))

    assert result.processing_status == "COMPLETED"
    assert result.result is not None
    assert result.result.date_of_incident.value == "NOT FOUND"
    assert "date_of_incident" in result.result.missing_fields
    assert "contact_information.client_or_family" in result.result.missing_fields
    assert result.result.human_review_required is True
    assert len(result.result.attorney_summary) == 5


def test_pipeline_returns_safe_failure_envelope():
    pipeline = PipelineService(FailingExtraction(), PassingReview())

    result = asyncio.run(pipeline.process(sample_requests()[0]))
    serialized = result.model_dump_json()

    assert result.processing_status == "FAILED"
    assert result.result is None
    assert result.errors[0].code == "MODEL_PROCESSING_FAILED"
    assert result.errors[0].retryable is True
    assert "secret upstream details" not in serialized


def test_invalid_raw_input_returns_non_retryable_failure():
    pipeline = PipelineService(FailingExtraction(), PassingReview())
    request = sample_requests()[0].model_copy(update={"payload": "bad transcript"})

    result = asyncio.run(pipeline.process(request))

    assert result.processing_status == "FAILED"
    assert result.errors[0].code == "INVALID_INPUT"
    assert result.source is None
