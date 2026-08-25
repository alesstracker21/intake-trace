from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


NOT_FOUND = "NOT FOUND"


class ProposalModel(BaseModel):
    """Gemini-compatible proposal base; deterministic code supplies strictness."""


class ScalarProposal(ProposalModel):
    value: str = Field(description="Exact supported value or the exact text NOT FOUND.")
    evidence_quotes: list[str] = Field(
        description="Verbatim source quotes supporting the value; empty for NOT FOUND."
    )


class ContactProposal(ProposalModel):
    type: Literal["phone", "email", "other"]
    value: str
    contact_name: str
    relationship_to_client: str
    evidence_quotes: list[str]


class FacilityProviderProposal(ProposalModel):
    name: str
    role: Literal[
        "incident_facility",
        "current_provider",
        "referring_provider",
        "other",
        "unknown",
    ]
    evidence_quotes: list[str]


class IntakeProposal(ProposalModel):
    potential_client_name: ScalarProposal
    contact_information: list[ContactProposal]
    facilities_or_providers: list[FacilityProviderProposal]
    date_of_incident: ScalarProposal
    injury_type: ScalarProposal
    referral_source: ScalarProposal


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictModel):
    quote: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class ScalarFact(StrictModel):
    value: str = Field(min_length=1)
    evidence: list[Evidence]
    validation_status: Literal["VERIFIED", "NOT_FOUND", "REJECTED_UNSUPPORTED"]


class ContactFact(StrictModel):
    type: Literal["phone", "email", "other"]
    value: str = Field(min_length=1)
    contact_name: str = Field(min_length=1)
    relationship_to_client: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class ContactCollection(StrictModel):
    items: list[ContactFact]
    validation_status: Literal["VERIFIED", "NOT_FOUND"]


class FacilityProviderFact(StrictModel):
    name: str = Field(min_length=1)
    role: Literal[
        "incident_facility",
        "current_provider",
        "referring_provider",
        "other",
        "unknown",
    ]
    evidence: list[Evidence] = Field(min_length=1)


class FacilityProviderCollection(StrictModel):
    items: list[FacilityProviderFact]
    validation_status: Literal["VERIFIED", "NOT_FOUND"]


class ValidatedFacts(StrictModel):
    potential_client_name: ScalarFact
    contact_information: ContactCollection
    facilities_or_providers: FacilityProviderCollection
    date_of_incident: ScalarFact
    injury_type: ScalarFact
    referral_source: ScalarFact


class ValidationIssue(StrictModel):
    path: str
    code: str
    message: str


class ValidationResult(StrictModel):
    validated_facts: ValidatedFacts
    missing_fields: list[str]
    validation_issues: list[ValidationIssue]
