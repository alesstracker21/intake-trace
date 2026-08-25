from __future__ import annotations

from copy import deepcopy

import pytest

from app.adapters import normalize_email, normalize_form, normalize_voicemail
from app.services.provenance import audit_provenance
from app.services.validation import validate_proposal


def _source(case_number, sample_text, sample_json):
    if case_number == 1:
        return normalize_voicemail(
            sample_text("01_voicemail_transcript.txt"), intake_id="INT-SYNTH-001"
        ).source_text
    if case_number == 2:
        return normalize_form(
            sample_json("02_web_form_submission.json"), intake_id="INT-SYNTH-002"
        ).source_text
    return normalize_email(
        sample_text("03_referral_email.eml"), intake_id="INT-SYNTH-003"
    ).source_text


@pytest.mark.parametrize("case_number", [1, 2, 3])
def test_all_accepted_evidence_has_exact_offsets(
    case_number, sample_text, sample_json, proposal_json
):
    source = _source(case_number, sample_text, sample_json)
    result = validate_proposal(source, proposal_json(case_number))

    assert audit_provenance(source, result) == []


def test_invented_date_and_contact_are_rejected(sample_text, sample_json, proposal_json):
    source = _source(3, sample_text, sample_json)
    result = validate_proposal(source, proposal_json(3))

    assert result.validated_facts.date_of_incident.value == "NOT FOUND"
    assert result.validated_facts.date_of_incident.validation_status == "REJECTED_UNSUPPORTED"
    assert [item.contact_name for item in result.validated_facts.contact_information.items] == [
        "Michael Chen"
    ]
    assert "contact_information.client_or_family" in result.missing_fields
    assert any(issue.code == "QUOTE_NOT_IN_SOURCE" for issue in result.validation_issues)


def test_value_outside_its_quote_is_rejected(sample_text, sample_json, proposal_json):
    proposal = deepcopy(proposal_json(1))
    proposal["injury_type"]["evidence_quotes"] = ["St. Anne's Hospital"]

    result = validate_proposal(_source(1, sample_text, sample_json), proposal)

    assert result.validated_facts.injury_type.value == "NOT FOUND"
    assert any(issue.code == "VALUE_NOT_IN_EVIDENCE" for issue in result.validation_issues)


def test_corrupted_offsets_fail_independent_provenance_audit(
    sample_text, sample_json, proposal_json
):
    source = _source(1, sample_text, sample_json)
    result = validate_proposal(source, proposal_json(1)).model_dump(mode="json")
    result["validated_facts"]["potential_client_name"]["evidence"][0]["start"] += 1

    assert audit_provenance(source, result)[0]["code"] == "QUOTE_OFFSET_MISMATCH"
