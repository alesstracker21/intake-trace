from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.facts import Evidence, ValidationIssue


class ReviewProposalModel(BaseModel):
    """Gemini-compatible model for advisory review output."""


class ReviewFinding(ReviewProposalModel):
    category: Literal[
        "UNSUPPORTED_FACT",
        "MISATTRIBUTION",
        "NEGATION_OR_UNCERTAINTY",
        "CONFLICT_IGNORED",
        "PROMPT_INJECTION",
        "MISSING_INFORMATION",
        "OTHER",
    ]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    source_quote: str
    explanation: str


class AdversarialReview(ReviewProposalModel):
    verdict: Literal["PASS", "REVIEW_REQUIRED", "FAIL"]
    prompt_injection_detected: bool
    extraction_grounded: bool
    findings: list[ReviewFinding]
    recommended_action: str


class InjectionSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    evidence: Evidence


class SafetyReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effective_verdict: Literal["PASS", "REVIEW_REQUIRED", "FAIL"]
    ai_verdict: Literal["PASS", "REVIEW_REQUIRED", "FAIL"]
    prompt_injection_detected: bool
    extraction_grounded: bool
    human_review_required: bool
    reason_codes: list[str]
    findings: list[ReviewFinding]
    review_quote_issues: list[ValidationIssue]
    deterministic_injection_signals: list[InjectionSignal]
