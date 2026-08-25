from __future__ import annotations

from app.models import AttorneySummary, NOT_FOUND, UrgencyResult, ValidationResult


def build_attorney_summary(
    validation: ValidationResult, urgency: UrgencyResult
) -> AttorneySummary:
    facts = validation.validated_facts
    client = _scalar(facts.potential_client_name)
    injury = _scalar(facts.injury_type)
    date = _scalar(facts.date_of_incident)
    referral = _scalar(facts.referral_source)
    incident_facility = _facility(facts.facilities_or_providers.items, "incident_facility")
    current_provider = _facility(facts.facilities_or_providers.items, "current_provider")

    sentence_groups = [
        _case_sentence(client, injury, incident_facility),
        _date_provider_sentence(date, current_provider),
        _contact_sentence(facts.contact_information.items),
        _referral_sentence(referral),
        _urgency_sentence(urgency),
    ]
    return AttorneySummary(
        sentences=[sentence for sentence, _ in sentence_groups],
        provenance=[
            {"sentence": index, "fact_paths": paths}
            for index, (_, paths) in enumerate(sentence_groups, start=1)
        ],
    )


def _case_sentence(client: str, injury: str, facility: str):
    paths = []
    if client != NOT_FOUND:
        paths.append("potential_client_name")
    if injury != NOT_FOUND:
        paths.append("injury_type")
    if facility != NOT_FOUND:
        paths.append("facilities_or_providers[incident_facility]")
    concise_injury = _concise_injury(injury)
    if client != NOT_FOUND and concise_injury != NOT_FOUND and facility != NOT_FOUND:
        return (
            f"{client} reportedly sustained {_with_article(concise_injury)} in a matter involving {facility}.",
            paths,
        )
    if client != NOT_FOUND and facility != NOT_FOUND:
        return f"The intake concerns {client} and {facility}.", paths
    if client != NOT_FOUND and concise_injury != NOT_FOUND:
        return f"{client} reportedly sustained {_with_article(concise_injury)}.", paths
    if client != NOT_FOUND:
        return f"The intake concerns potential client {client}.", paths
    return "The potential client was not identified.", paths


def _date_provider_sentence(date: str, provider: str):
    paths = []
    if date != NOT_FOUND:
        paths.append("date_of_incident")
    if provider != NOT_FOUND:
        paths.append("facilities_or_providers[current_provider]")
    if date != NOT_FOUND and provider != NOT_FOUND:
        return f"The incident date is {date}, and {provider} is the current provider.", paths
    if date != NOT_FOUND:
        return f"The incident date is {date}; no current provider was identified.", paths
    if provider != NOT_FOUND:
        return f"The incident date was not found; {provider} is the current provider.", paths
    return "The incident date and current provider were not found.", paths


def _contact_sentence(contacts):
    if not contacts:
        return "No contact information was found.", []
    client_contact = next(
        (
            (index, item)
            for index, item in enumerate(contacts)
            if not _is_referring_attorney(item.relationship_to_client)
        ),
        None,
    )
    if client_contact is None:
        contact = contacts[0]
        return (
            f"Only contact information for {contact.contact_name} ({contact.relationship_to_client}) is available.",
            ["contact_information[referring_attorney]"],
        )
    index, contact = client_contact
    if contact.contact_name == NOT_FOUND:
        return (
            f"A {contact.relationship_to_client} can be reached at {contact.value}.",
            [f"contact_information[{index}]"],
        )
    if contact.relationship_to_client.casefold() == "self":
        return f"{contact.contact_name} can be reached at {contact.value}.", [
            f"contact_information[{index}]"
        ]
    return (
        f"{contact.contact_name} ({contact.relationship_to_client}) can be reached at {contact.value}.",
        [f"contact_information[{index}]"],
    )


def _referral_sentence(referral: str):
    if referral == NOT_FOUND:
        return "No referral source was found.", []
    display = referral[3:] if referral.casefold().startswith("my ") else referral
    return f"The referral source is {display}.", ["referral_source"]


def _urgency_sentence(urgency: UrgencyResult):
    paths = ["urgency.flag", "urgency.rule_ids", "urgency.evidence"]
    rules = set(urgency.rule_ids)
    if urgency.flag == "URGENT":
        if {"TIME_SENSITIVE_SURGERY", "DOCUMENT_SIGNATURE_PRESSURE"}.issubset(rules):
            reason = "surgery is imminent and the facility is requesting a signature"
        elif "TIME_SENSITIVE_SURGERY" in rules:
            reason = "surgery is imminent"
        elif {"ACUTE_HOSPITAL_TRANSFER", "SERIOUS_INFECTION"} & rules:
            reason = "the source reports hospital transfer involving a serious infection"
        else:
            reason = "a configured urgent signal was identified"
        return f"Urgent attorney review is recommended because {reason}.", paths
    if urgency.flag == "REVIEW_REQUIRED":
        return "Attorney review is required because intake information is missing or unresolved.", paths
    return "Routine attorney review is recommended because no urgent signal was identified.", paths


def _scalar(fact) -> str:
    return fact.value if fact.validation_status == "VERIFIED" else NOT_FOUND


def _facility(items, role: str) -> str:
    return next((item.name for item in items if item.role == role), NOT_FOUND)


def _is_referring_attorney(relationship: str) -> bool:
    folded = relationship.casefold()
    return "attorney" in folded or "referr" in folded


def _with_article(value: str) -> str:
    if value.casefold().startswith(("a ", "an ", "the ")):
        return value
    return f"{'an' if value[0].casefold() in 'aeiou' else 'a'} {value}"


def _concise_injury(value: str) -> str:
    folded = value.casefold()
    for term in ("fractured hip", "pressure ulcer", "serious infection"):
        if term in folded:
            return term
    return value if len(value) <= 60 else "reported injury"
