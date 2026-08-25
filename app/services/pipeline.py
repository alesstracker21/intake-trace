from __future__ import annotations

import logging
import uuid

from opentelemetry.trace import Status, StatusCode

from app.adapters import normalize_email, normalize_form, normalize_voicemail
from app.models import Channel, ExecutionEnvelope, IntakeRequest, NormalizedIntake
from app.observability import current_trace_id, get_tracer
from app.services.assembly import assemble_completed_output, assemble_failed_output
from app.services.provenance import audit_provenance
from app.services.summary import build_attorney_summary
from app.services.urgency import assess_urgency
from app.services.validation import validate_proposal


logger = logging.getLogger(__name__)
tracer = get_tracer()


class ProvenanceIntegrityError(RuntimeError):
    pass


class PipelineService:
    def __init__(self, extraction_service, review_service) -> None:
        self._extraction = extraction_service
        self._review = review_service

    async def process(self, request: IntakeRequest) -> ExecutionEnvelope:
        intake_id = request.intake_id or f"INT-{uuid.uuid4().hex[:12].upper()}"
        normalized: NormalizedIntake | None = None
        stage = "normalization"
        with tracer.start_as_current_span("intake.processing") as root_span:
            trace_id = current_trace_id()
            root_span.set_attributes(
                {
                    "intake.id": intake_id,
                    "intake.source.type": request.channel.value,
                }
            )
            try:
                with tracer.start_as_current_span("intake.normalization") as span:
                    normalized = normalize_request(request, intake_id=intake_id)
                    span.set_attributes(
                        {
                            "intake.source.provider": normalized.source.provider,
                            "intake.source.character_count": len(normalized.source_text),
                        }
                    )

                stage = "extraction"
                with tracer.start_as_current_span("intake.ai_extraction") as span:
                    proposal, extraction_events = await self._extraction.propose(
                        normalized, trace_id
                    )
                    span.set_attribute("adk.event.count", extraction_events)

                stage = "evidence_validation"
                with tracer.start_as_current_span("intake.evidence_validation") as span:
                    validation = validate_proposal(normalized.source_text, proposal)
                    span.set_attributes(
                        {
                            "validation.missing_field.count": len(validation.missing_fields),
                            "validation.issue.count": len(validation.validation_issues),
                        }
                    )

                stage = "provenance_audit"
                with tracer.start_as_current_span("intake.provenance_audit") as span:
                    provenance_issues = audit_provenance(normalized.source_text, validation)
                    span.set_attribute("provenance.issue.count", len(provenance_issues))
                    if provenance_issues:
                        raise ProvenanceIntegrityError("validated evidence failed audit")

                stage = "adversarial_review"
                with tracer.start_as_current_span("intake.adversarial_review") as span:
                    review, review_events = await self._review.review(
                        normalized, proposal, validation, trace_id
                    )
                    span.set_attributes(
                        {
                            "adk.event.count": review_events,
                            "review.effective_verdict": review.effective_verdict,
                            "review.prompt_injection_detected": review.prompt_injection_detected,
                        }
                    )

                stage = "urgency_assessment"
                with tracer.start_as_current_span("intake.urgency_assessment") as span:
                    urgency = assess_urgency(normalized.source_text, validation)
                    span.set_attributes(
                        {
                            "intake.urgency.flag": urgency.flag,
                            "intake.urgency.rule.count": len(urgency.rule_ids),
                        }
                    )

                stage = "summary_creation"
                with tracer.start_as_current_span("intake.summary_creation") as span:
                    summary = build_attorney_summary(validation, urgency)
                    span.set_attribute("summary.sentence.count", len(summary.sentences))

                stage = "output_assembly"
                with tracer.start_as_current_span("intake.output_assembly"):
                    output = assemble_completed_output(
                        normalized,
                        validation,
                        provenance_issues,
                        review,
                        urgency,
                        summary,
                        trace_id,
                    )
                root_span.set_attributes(
                    {
                        "intake.processing_status": "COMPLETED",
                        "intake.human_review_required": output.result.human_review_required,
                    }
                )
                return output
            except ValueError:
                root_span.set_status(Status(StatusCode.ERROR))
                root_span.set_attribute("intake.processing_status", "FAILED")
                root_span.set_attribute("intake.failure.stage", stage)
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
                root_span.set_status(Status(StatusCode.ERROR))
                root_span.set_attribute("intake.processing_status", "FAILED")
                root_span.set_attribute("intake.failure.stage", stage)
                return self._unexpected_failure(intake_id, trace_id, normalized, stage)

    @staticmethod
    def _unexpected_failure(
        intake_id: str,
        trace_id: str,
        normalized: NormalizedIntake | None,
        stage: str,
    ) -> ExecutionEnvelope:
        logger.error("Intake processing failed at stage %s", stage)
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
