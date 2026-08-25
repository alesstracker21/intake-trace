from __future__ import annotations

from typing import Any

from app.models import ValidationResult


def audit_provenance(
    source_text: str, validation: ValidationResult | dict[str, Any]
) -> list[dict[str, str]]:
    raw = validation.model_dump(mode="json") if isinstance(validation, ValidationResult) else validation
    issues: list[dict[str, str]] = []
    facts = raw.get("validated_facts")
    if not isinstance(facts, dict):
        return [_issue("validated_facts", "MISSING_VALIDATED_FACTS", "Facts must be an object.")]
    _walk(source_text, facts, "validated_facts", issues)
    return issues


def _walk(source_text: str, value: Any, path: str, issues: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        if {"quote", "start", "end"}.issubset(value):
            _audit_item(source_text, value, path, issues)
            return
        for key, child in value.items():
            _walk(source_text, child, f"{path}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(source_text, child, f"{path}[{index}]", issues)


def _audit_item(
    source_text: str, evidence: dict[str, Any], path: str, issues: list[dict[str, str]]
) -> None:
    quote, start, end = evidence.get("quote"), evidence.get("start"), evidence.get("end")
    if not isinstance(quote, str) or not isinstance(start, int) or not isinstance(end, int):
        issues.append(_issue(path, "MALFORMED_PROVENANCE", "Evidence fields have invalid types."))
    elif start < 0 or end <= start or end > len(source_text):
        issues.append(_issue(path, "INVALID_OFFSETS", "Evidence offsets are outside source text."))
    elif source_text[start:end] != quote:
        issues.append(
            _issue(path, "QUOTE_OFFSET_MISMATCH", "The source slice does not equal the quote.")
        )


def _issue(path: str, code: str, message: str) -> dict[str, str]:
    return {"path": path, "code": code, "message": message}
