from __future__ import annotations

import pytest

from app.adapters import normalize_email, normalize_form, normalize_voicemail
from app.models import Channel


def test_voicemail_adapter_preserves_transcript_and_metadata(sample_text):
    normalized = normalize_voicemail(
        sample_text("01_voicemail_transcript.txt"), intake_id="INT-SYNTH-001"
    )

    assert normalized.source.type == Channel.VOICEMAIL
    assert normalized.source.external_id == "CALL-SYNTH-001"
    assert normalized.source_text.startswith("Hi, um, my name is Lila Desai.")
    assert "Call ID:" not in normalized.source_text


def test_form_adapter_renders_a_stable_evidence_source(sample_json):
    normalized = normalize_form(
        sample_json("02_web_form_submission.json"), intake_id="INT-SYNTH-002"
    )

    assert normalized.source.type == Channel.WEB_FORM
    assert "Potential client name: Camille Turner" in normalized.source_text
    assert "Phone: NOT PROVIDED" in normalized.source_text
    assert "Consent to contact: Yes" in normalized.source_text


def test_email_adapter_separates_headers_and_body(sample_text):
    normalized = normalize_email(
        sample_text("03_referral_email.eml"), intake_id="INT-SYNTH-003"
    )

    assert normalized.source.type == Channel.REFERRAL_EMAIL
    assert normalized.source.external_id == "referral-synth-003@chen-soto.example.test"
    assert normalized.source_text.startswith("From: Michael Chen")
    assert "To: Intake Team" not in normalized.source_text
    assert "I do not yet have the date" in normalized.source_text


@pytest.mark.parametrize(
    "normalizer, raw",
    [
        (normalize_voicemail, "not a transcript"),
        (normalize_email, "Subject: missing headers\n\nbody"),
    ],
)
def test_text_adapters_reject_malformed_inputs(normalizer, raw):
    with pytest.raises(ValueError):
        normalizer(raw, intake_id="INT-BAD")


def test_form_adapter_rejects_missing_fields_object():
    with pytest.raises(ValueError, match="fields object"):
        normalize_form({}, intake_id="INT-BAD")
