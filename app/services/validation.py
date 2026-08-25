from __future__ import annotations

from typing import Any

from app.models import NOT_FOUND, IntakeProposal, ValidationResult


SCALAR_FIELDS = (
    "potential_client_name",
    "date_of_incident",
    "injury_type",
    "referral_source",
)
ALLOWED_CONTACT_TYPES = {"phone", "email", "other"}
ALLOWED_FACILITY_ROLES = {
    "incident_facility",
    "current_provider",
    "referring_provider",
    "other",
    "unknown",
}


def validate_proposal(
    source_text: str, proposal: IntakeProposal | dict[str, Any]
) -> ValidationResult:
    raw = proposal.model_dump(mode="json") if isinstance(proposal, IntakeProposal) else proposal
    issues: list[dict[str, str]] = []
    missing_fields: list[str] = []
    facts: dict[str, Any] = {}

    for field_name in SCALAR_FIELDS:
        fact = _validate_scalar(source_text, raw.get(field_name), field_name, issues)
        facts[field_name] = fact
        if fact["validation_status"] != "VERIFIED":
            missing_fields.append(field_name)

    contacts = _validate_contacts(source_text, raw.get("contact_information"), issues)
    facts["contact_information"] = contacts
    if contacts["validation_status"] == "NOT_FOUND":
        missing_fields.append("contact_information")
    elif not _has_client_or_family_contact(contacts["items"]):
        missing_fields.append("contact_information.client_or_family")

    facilities = _validate_facilities(source_text, raw.get("facilities_or_providers"), issues)
    facts["facilities_or_providers"] = facilities
    if facilities["validation_status"] == "NOT_FOUND":
        missing_fields.append("facilities_or_providers")

    return ValidationResult.model_validate(
        {
            "validated_facts": facts,
            "missing_fields": missing_fields,
            "validation_issues": issues,
        }
    )


def _validate_scalar(
    source_text: str,
    proposed: Any,
    path: str,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    if not isinstance(proposed, dict):
        _add_issue(issues, path, "MISSING_PROPOSAL", "The proposal is missing or malformed.")
        return _rejected_scalar()

    value = proposed.get("value")
    quotes = proposed.get("evidence_quotes")
    if not isinstance(value, str) or not value.strip() or not isinstance(quotes, list):
        _add_issue(issues, path, "MALFORMED_PROPOSAL", "Value or evidence is malformed.")
        return _rejected_scalar()

    value = value.strip()
    if value == NOT_FOUND:
        if quotes:
            _add_issue(
                issues,
                path,
                "NOT_FOUND_WITH_EVIDENCE",
                "A NOT FOUND proposal must not include evidence.",
            )
        return {"value": NOT_FOUND, "evidence": [], "validation_status": "NOT_FOUND"}

    evidence = _locate_quotes(source_text, quotes, path, issues)
    if evidence is None or not _text_is_supported(value, quotes):
        if evidence is not None:
            _add_issue(
                issues,
                path,
                "VALUE_NOT_IN_EVIDENCE",
                "The proposed value does not occur in its evidence.",
            )
        return _rejected_scalar()

    return {"value": value, "evidence": evidence, "validation_status": "VERIFIED"}


def _validate_contacts(
    source_text: str, proposed: Any, issues: list[dict[str, str]]
) -> dict[str, Any]:
    if not isinstance(proposed, list):
        _add_issue(
            issues,
            "contact_information",
            "MALFORMED_COLLECTION",
            "Contact information must be a list.",
        )
        return {"items": [], "validation_status": "NOT_FOUND"}

    accepted: list[dict[str, Any]] = []
    for index, item in enumerate(proposed):
        path = f"contact_information[{index}]"
        if not isinstance(item, dict):
            _add_issue(issues, path, "MALFORMED_ITEM", "Contact item must be an object.")
            continue

        contact_type = item.get("type")
        value = item.get("value")
        name = item.get("contact_name")
        relationship = item.get("relationship_to_client")
        quotes = item.get("evidence_quotes")
        if contact_type not in ALLOWED_CONTACT_TYPES or not all(
            isinstance(part, str) and part.strip() for part in (value, name, relationship)
        ):
            _add_issue(issues, path, "MALFORMED_ITEM", "Contact fields are invalid.")
            continue

        evidence = _locate_quotes(source_text, quotes, path, issues)
        name_supported = name == NOT_FOUND or _text_is_supported(name, quotes)
        relationship_supported = _relationship_is_supported(relationship, quotes)
        if (
            evidence is None
            or not _text_is_supported(value, quotes)
            or not name_supported
            or not relationship_supported
        ):
            if evidence is not None:
                _add_issue(
                    issues,
                    path,
                    "CONTACT_NOT_IN_EVIDENCE",
                    "The contact value, owner, or relationship is not supported by its evidence.",
                )
            continue

        accepted.append(
            {
                "type": contact_type,
                "value": value.strip(),
                "contact_name": name.strip(),
                "relationship_to_client": relationship.strip(),
                "evidence": evidence,
            }
        )

    return {
        "items": accepted,
        "validation_status": "VERIFIED" if accepted else "NOT_FOUND",
    }


def _validate_facilities(
    source_text: str, proposed: Any, issues: list[dict[str, str]]
) -> dict[str, Any]:
    if not isinstance(proposed, list):
        _add_issue(
            issues,
            "facilities_or_providers",
            "MALFORMED_COLLECTION",
            "Facilities or providers must be a list.",
        )
        return {"items": [], "validation_status": "NOT_FOUND"}

    accepted: list[dict[str, Any]] = []
    for index, item in enumerate(proposed):
        path = f"facilities_or_providers[{index}]"
        if not isinstance(item, dict):
            _add_issue(issues, path, "MALFORMED_ITEM", "Facility item must be an object.")
            continue
        name = item.get("name")
        role = item.get("role")
        quotes = item.get("evidence_quotes")
        if not isinstance(name, str) or not name.strip() or role not in ALLOWED_FACILITY_ROLES:
            _add_issue(issues, path, "MALFORMED_ITEM", "Facility name or role is invalid.")
            continue
        evidence = _locate_quotes(source_text, quotes, path, issues)
        if evidence is None or not _text_is_supported(name, quotes):
            if evidence is not None:
                _add_issue(
                    issues,
                    path,
                    "FACILITY_NOT_IN_EVIDENCE",
                    "The facility name does not occur in its evidence.",
                )
            continue
        accepted.append({"name": name.strip(), "role": role, "evidence": evidence})

    return {
        "items": accepted,
        "validation_status": "VERIFIED" if accepted else "NOT_FOUND",
    }


def _locate_quotes(
    source_text: str, quotes: Any, path: str, issues: list[dict[str, str]]
) -> list[dict[str, Any]] | None:
    if not isinstance(quotes, list) or not quotes:
        _add_issue(issues, path, "MISSING_EVIDENCE", "At least one evidence quote is required.")
        return None
    evidence: list[dict[str, Any]] = []
    for quote in quotes:
        if not isinstance(quote, str) or not quote:
            _add_issue(issues, path, "MALFORMED_EVIDENCE", "Evidence must be non-empty text.")
            return None
        start = source_text.find(quote)
        if start < 0:
            _add_issue(
                issues,
                path,
                "QUOTE_NOT_IN_SOURCE",
                "An evidence quote was not found exactly in the normalized source.",
            )
            return None
        evidence.append({"quote": quote, "start": start, "end": start + len(quote)})
    return evidence


def _text_is_supported(value: str, quotes: Any) -> bool:
    if not isinstance(quotes, list):
        return False
    evidence_text = "\n".join(quote for quote in quotes if isinstance(quote, str))
    return value.casefold() in evidence_text.casefold()


def _relationship_is_supported(relationship: str, quotes: Any) -> bool:
    folded = relationship.casefold()
    evidence = "\n".join(quote for quote in quotes if isinstance(quote, str)).casefold()
    if folded == "self":
        return "self" in evidence
    if "attorney" in folded or "referr" in folded:
        return "referral" in evidence or "attorney" in evidence
    return folded in evidence


def _has_client_or_family_contact(items: list[dict[str, Any]]) -> bool:
    return any(
        "attorney" not in item["relationship_to_client"].casefold()
        and "referr" not in item["relationship_to_client"].casefold()
        for item in items
    )


def _rejected_scalar() -> dict[str, Any]:
    return {"value": NOT_FOUND, "evidence": [], "validation_status": "REJECTED_UNSUPPORTED"}


def _add_issue(
    issues: list[dict[str, str]], path: str, code: str, message: str
) -> None:
    issues.append({"path": path, "code": code, "message": message})
