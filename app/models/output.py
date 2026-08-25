from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.facts import ValidatedFacts, ValidationIssue
from app.models.intake import SourceMetadata
from app.models.review import SafetyReviewResult
from app.models.triage import SummaryProvenance, UrgencyResult


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CanonicalResult(ValidatedFacts):
    urgency: UrgencyResult
    missing_fields: list[str]
    validation_issues: list[ValidationIssue]
    provenance_issues: list[ValidationIssue]
    safety_review: SafetyReviewResult
    human_review_required: bool
    human_review_reasons: list[str]
    attorney_summary: list[str] = Field(min_length=5, max_length=5)
    summary_provenance: list[SummaryProvenance] = Field(min_length=5, max_length=5)


class ErrorInformation(StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool


class ExecutionEnvelope(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    intake_id: str = Field(min_length=1)
    source: SourceMetadata | None
    trace_id: str = Field(min_length=32, max_length=32)
    processing_status: Literal["COMPLETED", "FAILED"]
    result: CanonicalResult | None
    errors: list[ErrorInformation]

    @model_validator(mode="after")
    def status_matches_payload(self) -> "ExecutionEnvelope":
        if self.processing_status == "COMPLETED" and (self.result is None or self.errors):
            raise ValueError("completed processing requires a result and no errors")
        if self.processing_status == "FAILED" and (self.result is not None or not self.errors):
            raise ValueError("failed processing requires errors and no result")
        return self
