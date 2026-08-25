from __future__ import annotations

from typing import Any, Mapping

from app.adapters.common import required
from app.models import Channel, NormalizedIntake, SourceMetadata


FORM_FIELD_LABELS = {
    "potential_client_name": "Potential client name",
    "relationship_to_client": "Relationship to potential client",
    "email": "Email",
    "phone": "Phone",
    "facility_or_provider": "Facility or provider",
    "date_of_incident": "Date of incident",
    "injury_description": "Injury description",
    "referral_source": "Referral source",
    "additional_details": "Additional details",
    "consent_to_contact": "Consent to contact",
}


def normalize_form(payload: Mapping[str, Any], *, intake_id: str) -> NormalizedIntake:
    fields = payload.get("fields")
    if not isinstance(fields, Mapping):
        raise ValueError("form payload must contain a fields object")

    source_text = "\n".join(
        f"{label}: {_render_form_value(fields.get(key))}"
        for key, label in FORM_FIELD_LABELS.items()
    )
    return NormalizedIntake(
        intake_id=intake_id,
        source=SourceMetadata(
            type=Channel.WEB_FORM,
            provider=required(payload, "provider"),
            external_id=required(payload, "submission_id"),
            received_at=required(payload, "submitted_at"),
        ),
        source_text=source_text,
    )


def _render_form_value(value: Any) -> str:
    if value is None or value == "":
        return "NOT PROVIDED"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).strip()
