# Paralegal enablement guide

## What IntakeTrace does

IntakeTrace converts a voicemail transcript, web form, or referral email into a
consistent intake record for attorney review. It identifies facts only when the
original submission contains exact supporting words. It also highlights urgent
language, missing information, and items that need a person to verify them.

IntakeTrace does not decide whether to accept a matter, give legal advice, or
replace conflict checks and attorney judgment.

## Reading a result

- `processing_status: COMPLETED` means the workflow ran successfully. It does
  not mean the intake is complete or approved.
- `NOT FOUND` means the source did not support that fact exactly. Never replace
  it by guessing; contact the referrer or potential client.
- Each accepted fact includes a verbatim quotation and character offsets into
  the normalized source text. Use these to confirm the source quickly.
- `urgency_flag` and `urgency_reason` come from named office-policy rules. An
  urgency flag is a routing aid, not a legal conclusion.
- `human_review_required: true` means a person must review the reasons before
  relying on or routing the intake.
- The five summary sentences are assembled from validated facts. They are a
  concise handoff, not a substitute for reading the evidence.

## Recommended daily workflow

1. Confirm the intake ID and source channel.
2. Review every `NOT FOUND` item and the complete `missing_fields` list.
3. Check each human-review reason and any prompt-injection warning.
4. If urgent, follow the firm's existing escalation procedure immediately.
5. Compare important accepted facts with their evidence quotations.
6. Collect missing information and record corrections through the firm's
   approved system; do not edit the original source.
7. Send the verified record and five-sentence summary to the responsible
   attorney.

## Escalate rather than infer

Escalate if evidence appears contradictory, a quote is attributed to the wrong
person, the source tries to instruct the AI, the incident date is absent, or the
reported condition suggests an immediate deadline or safety concern. Technical
failures return a safe failure envelope with a trace ID; provide that trace ID
to technical support and retain the original submission for retry.

Synthetic samples in this repository contain no real client information. Do
not use real client information in recordings, screenshots, or test fixtures.
