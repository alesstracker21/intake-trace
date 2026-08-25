from __future__ import annotations

import logging
import uuid

from app.adapters import normalize_email, normalize_form, normalize_voicemail
from app.models import Channel, ExecutionEnvelope, IntakeRequest, NormalizedIntake
from app.services.assembly import assemble_completed_output, assemble_failed_output
from app.services.provenance import audit_provenance
from app.services.summary import build_attorney_summary
from app.services.urgency import assess_urgency
from app.services.validation import validate_proposal


logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, extraction_service, review_service) -> None:
        self._extraction = extraction_service
        self._review = review_service

    async def process(self, request: IntakeRequest) -> ExecutionEnvelope:
        trace_id = uuid.uuid4().hex
        intake_id = request.intake_id or f"INT-{uuid.uuid4().hex[:12].upper()}"
        normalized: NormalizedIntake | None = None
        stage = "normalization"
        try:
            normalized = normalize_request(request, intake_id=intake_id)

            stage = "extraction"
            proposal, _ = await self._extraction.propose(normalized, trace_id)

            stage = "evidence_validation"
            validation = validate_proposal(normalized.source_text, proposal)

            stage = "provenance_audit"
            provenance_issues = audit_provenance(normalized.source_text, validation)
            if provenance_issues:
                raise RuntimeError("provenance audit failed")

            stage = "adversarial_review"
            review, _ = await self._review.review(normalized, proposal, validation, trace_id)

            stage = "urgency_assessment"
            urgency = assess_urgency(normalized.source_text, validation)

            stage = "summary_creation"
            summary = build_attorney_summary(validation, urgency)

            stage = "output_assembly"
            return assemble_completed_output(
                normalized,
                validation,
                provenance_issues,
                review,
                urgency,
                summary,
                trace_id,
            )
        except ValueError:
            if stage == "normalization":
                logger.info("Rejected malformed intake", extra={"intake_id": intake_id})
                return assemble_failed_output(
                    intake_id=intake_id,
                    trace_id=trace_id,
                    code="INVALID_INPUT",
                    message="The raw intake does not match the selected channel contract.",
                    retryable=False,
                    normalized=normalized,
                )
            return self._unexpected_failure(intake_id, trace_id, normalized, stage)
        except Exception:
            return self._unexpected_failure(intake_id, trace_id, normalized, stage)

    @staticmethod
    def _unexpected_failure(
        intake_id: str,
        trace_id: str,
        normalized: NormalizedIntake | None,
        stage: str,
    ) -> ExecutionEnvelope:
        logger.exception("Intake processing failed at stage %s", stage)
        if stage in {"extraction", "adversarial_review"}:
            code = "MODEL_PROCESSING_FAILED"
            message = "The AI service could not produce a reliable structured response."
            retryable = True
        elif stage == "provenance_audit":
            code = "PROVENANCE_AUDIT_FAILED"
            message = "Evidence integrity checks failed; no result was released."
            retryable = False
        else:
            code = "PROCESSING_FAILED"
            message = "The workflow could not produce a reliable result."
            retryable = False
        return assemble_failed_output(
            intake_id=intake_id,
            trace_id=trace_id,
            code=code,
            message=message,
            retryable=retryable,
            normalized=normalized,
        )


def normalize_request(request: IntakeRequest, *, intake_id: str) -> NormalizedIntake:
    if request.channel == Channel.VOICEMAIL:
        assert isinstance(request.payload, str)
        return normalize_voicemail(request.payload, intake_id=intake_id)
    if request.channel == Channel.WEB_FORM:
        assert isinstance(request.payload, dict)
        return normalize_form(request.payload, intake_id=intake_id)
    assert isinstance(request.payload, str)
    return normalize_email(request.payload, intake_id=intake_id)
