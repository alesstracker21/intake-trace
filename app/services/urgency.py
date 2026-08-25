from __future__ import annotations

from dataclasses import dataclass

from app.models import UrgencyResult, ValidationResult


@dataclass(frozen=True)
class SourceRule:
    rule_id: str
    phrases: tuple[str, ...]
    reason: str


URGENT_SOURCE_RULES = (
    SourceRule(
        "TIME_SENSITIVE_SURGERY",
        ("needs surgery tomorrow", "surgery tomorrow morning"),
        "The source reports surgery scheduled for the next day.",
    ),
    SourceRule(
        "DOCUMENT_SIGNATURE_PRESSURE",
        ("asking me to sign", "asked me to sign"),
        "The source reports pressure to sign a document.",
    ),
    SourceRule(
        "ACUTE_HOSPITAL_TRANSFER",
        (
            "transferred to a hospital with a serious infection",
            "transferred to the hospital with a serious infection",
        ),
        "The source reports a hospital transfer involving a serious infection.",
    ),
)


def assess_urgency(source_text: str, validation: ValidationResult) -> UrgencyResult:
    rule_ids: list[str] = []
    reasons: list[str] = []
    evidence: list[dict] = []

    for rule in URGENT_SOURCE_RULES:
        match = _find_first_phrase(source_text, rule.phrases)
        if match:
            quote, start, end = match
            rule_ids.append(rule.rule_id)
            reasons.append(rule.reason)
            evidence.append({"quote": quote, "start": start, "end": end})

    injury = validation.validated_facts.injury_type
    if injury.validation_status == "VERIFIED" and injury.value.casefold() == "serious infection":
        rule_ids.append("SERIOUS_INFECTION")
        reasons.append("The validated injury is described as a serious infection.")
        evidence.extend(item.model_dump(mode="json") for item in injury.evidence)

    if rule_ids:
        return UrgencyResult(
            flag="URGENT",
            reason=" ".join(dict.fromkeys(reasons)),
            rule_ids=list(dict.fromkeys(rule_ids)),
            evidence=_deduplicate_evidence(evidence),
        )
    if validation.missing_fields or validation.validation_issues:
        review_rules: list[str] = []
        reason_parts: list[str] = []
        if validation.missing_fields:
            review_rules.append("MISSING_REQUIRED_INFORMATION")
            reason_parts.append("Required intake information is missing.")
        if validation.validation_issues:
            review_rules.append("VALIDATION_ISSUES_PRESENT")
            reason_parts.append("One or more proposed facts failed validation.")
        return UrgencyResult(
            flag="REVIEW_REQUIRED",
            reason=" ".join(reason_parts),
            rule_ids=review_rules,
            evidence=[],
        )
    return UrgencyResult(
        flag="ROUTINE",
        reason="No configured urgent signal or review condition was found.",
        rule_ids=["NO_URGENT_SIGNAL"],
        evidence=[],
    )


def _find_first_phrase(source_text: str, phrases: tuple[str, ...]):
    folded = source_text.casefold()
    matches: list[tuple[int, str]] = []
    for phrase in phrases:
        start = folded.find(phrase.casefold())
        if start >= 0:
            matches.append((start, source_text[start : start + len(phrase)]))
    if not matches:
        return None
    start, quote = min(matches, key=lambda item: item[0])
    return quote, start, start + len(quote)


def _deduplicate_evidence(items: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[tuple[str, int, int]] = set()
    for item in items:
        key = (item["quote"], item["start"], item["end"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
