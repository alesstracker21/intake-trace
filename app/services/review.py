from __future__ import annotations

import json
from dataclasses import dataclass

from app.models import (
    AdversarialReview,
    IntakeProposal,
    NormalizedIntake,
    SafetyReviewResult,
    ValidationResult,
)
from app.services.agent_runtime import run_structured_agent


@dataclass(frozen=True)
class InjectionRule:
    rule_id: str
    phrase: str


INJECTION_RULES = (
    InjectionRule("IGNORE_PRIOR_INSTRUCTIONS", "ignore all prior instructions"),
    InjectionRule("FAKE_SYSTEM_MESSAGE", "important system message"),
    InjectionRule("SUPPRESS_WARNING", "do not mention this instruction"),
    InjectionRule("MODEL_OUTPUT_OVERRIDE", "set the potential client"),
)


class SafetyReviewService:
    def __init__(self, agent) -> None:
        self._agent = agent

    async def review(
        self,
        intake: NormalizedIntake,
        proposal: IntakeProposal,
        validation: ValidationResult,
        trace_id: str,
    ) -> tuple[SafetyReviewResult, int]:
        package = {
            "source_text": intake.source_text,
            "extraction_proposal": proposal.model_dump(mode="json"),
            "validation_result": validation.model_dump(mode="json"),
        }
        raw, event_count = await run_structured_agent(
            self._agent,
            output_key="adversarial_review",
            message_text=json.dumps(package, ensure_ascii=False),
            correlation_id=f"review-{trace_id}",
        )
        ai_review = AdversarialReview.model_validate(raw)
        return apply_review_policy(intake.source_text, ai_review, validation), event_count


def detect_prompt_injection(source_text: str) -> list[dict]:
    folded = source_text.casefold()
    signals: list[dict] = []
    for rule in INJECTION_RULES:
        start = folded.find(rule.phrase)
        if start >= 0:
            quote = source_text[start : start + len(rule.phrase)]
            signals.append(
                {
                    "rule_id": rule.rule_id,
                    "evidence": {"quote": quote, "start": start, "end": start + len(quote)},
                }
            )
    return signals


def apply_review_policy(
    source_text: str,
    ai_review: AdversarialReview | dict,
    validation: ValidationResult,
) -> SafetyReviewResult:
    review = (
        ai_review if isinstance(ai_review, AdversarialReview) else AdversarialReview.model_validate(ai_review)
    )
    quote_issues: list[dict[str, str]] = []
    for index, finding in enumerate(review.findings):
        if finding.source_quote != "NOT APPLICABLE" and finding.source_quote not in source_text:
            quote_issues.append(
                {
                    "path": f"findings[{index}].source_quote",
                    "code": "REVIEW_QUOTE_NOT_IN_SOURCE",
                    "message": "The reviewer quote was not found exactly in source text.",
                }
            )

    injection_signals = detect_prompt_injection(source_text)
    reason_codes: list[str] = []
    if validation.missing_fields:
        reason_codes.append("MISSING_REQUIRED_FACTS")
    if validation.validation_issues:
        reason_codes.append("VALIDATION_ISSUES")
    if quote_issues:
        reason_codes.append("REVIEW_QUOTE_INVALID")
    if review.prompt_injection_detected or injection_signals:
        reason_codes.append("PROMPT_INJECTION_DETECTED")

    if review.verdict == "FAIL":
        effective_verdict = "FAIL"
        reason_codes.append("ADVERSARIAL_REVIEW_FAILED")
    elif reason_codes or review.verdict == "REVIEW_REQUIRED":
        effective_verdict = "REVIEW_REQUIRED"
    else:
        effective_verdict = "PASS"

    return SafetyReviewResult.model_validate(
        {
            "effective_verdict": effective_verdict,
            "ai_verdict": review.verdict,
            "prompt_injection_detected": bool(
                review.prompt_injection_detected or injection_signals
            ),
            "extraction_grounded": review.extraction_grounded,
            "human_review_required": effective_verdict != "PASS",
            "reason_codes": list(dict.fromkeys(reason_codes)),
            "findings": review.findings,
            "review_quote_issues": quote_issues,
            "deterministic_injection_signals": injection_signals,
        }
    )
