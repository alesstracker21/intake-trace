from __future__ import annotations

from app.models import (
    AttorneySummary,
    CanonicalResult,
    ExecutionEnvelope,
    NormalizedIntake,
    SafetyReviewResult,
    UrgencyResult,
    ValidationResult,
)


def assemble_completed_output(
    intake: NormalizedIntake,
    validation: ValidationResult,
    provenance_issues: list[dict[str, str]],
    review: SafetyReviewResult,
    urgency: UrgencyResult,
    summary: AttorneySummary,
    trace_id: str,
) -> ExecutionEnvelope:
    review_reasons = list(review.reason_codes)
    if urgency.flag == "URGENT":
        review_reasons.append("URGENT_ROUTING")
    elif urgency.flag == "REVIEW_REQUIRED":
        review_reasons.append("URGENCY_REVIEW_REQUIRED")
    if provenance_issues:
        review_reasons.append("PROVENANCE_INTEGRITY_FAILED")
    review_reasons = list(dict.fromkeys(review_reasons))

    result = CanonicalResult.model_validate(
        {
            **validation.validated_facts.model_dump(mode="json"),
            "urgency": urgency,
            "missing_fields": validation.missing_fields,
            "validation_issues": validation.validation_issues,
            "provenance_issues": provenance_issues,
            "safety_review": review,
            "human_review_required": bool(
                review_reasons
                or validation.missing_fields
                or validation.validation_issues
                or urgency.flag != "ROUTINE"
            ),
            "human_review_reasons": review_reasons,
            "attorney_summary": summary.sentences,
            "summary_provenance": summary.provenance,
        }
    )
    return ExecutionEnvelope(
        intake_id=intake.intake_id,
        source=intake.source,
        trace_id=trace_id,
        processing_status="COMPLETED",
        result=result,
        errors=[],
    )


def assemble_failed_output(
    *,
    intake_id: str,
    trace_id: str,
    code: str,
    message: str,
    retryable: bool,
    normalized: NormalizedIntake | None = None,
) -> ExecutionEnvelope:
    return ExecutionEnvelope(
        intake_id=intake_id,
        source=normalized.source if normalized else None,
        trace_id=trace_id,
        processing_status="FAILED",
        result=None,
        errors=[{"code": code, "message": message, "retryable": retryable}],
    )
