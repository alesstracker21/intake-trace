# IntakeTrace: quick guide for intake staff

## What this tool does

IntakeTrace turns a website form, referral email, or voicemail transcript into one organized intake record. It pulls out names, contact details, dates, facilities, injuries, and the referral source. It also marks urgent language, lists missing information, and prepares a five-sentence summary for an attorney.

The tool helps with intake preparation. It does not accept or reject a matter, give legal advice, run a conflict check, or replace attorney review.

## Connecting a form, email, or transcript

The assessment service is available at:

`https://intake-trace-sqkre4xmpa-uc.a.run.app`

- Check that it is online: `GET /health`
- Send an intake for processing: `POST /v1/intakes`
- Open the built-in testing screen: `/docs`

The person who manages the website form or office automation should send each submission to the intake endpoint. The submission must identify its type as `web_form`, `referral_email`, or `voicemail` and include the original form fields, email, or transcript. All three types return the same organized result.

To try it manually, open `/docs`, choose `POST /v1/intakes`, select **Try it out**, enter a sample request, and select **Execute**. The current public address is for synthetic assessment data only. Do not send real client information until the firm has approved access controls and privacy safeguards.

## How to read the result

- `COMPLETED` means the tool finished. It does not mean the matter was approved or the intake is complete.
- `NOT FOUND` means the original submission did not contain enough support for that item. Contact the potential client or referrer instead of guessing.
- `URGENT` means a configured warning rule found time-sensitive wording. Follow the firm's normal escalation process immediately.
- `human_review_required: true` means a person must review the listed reasons before the result is relied upon.
- **Evidence** shows the exact words from the original submission that support each accepted fact.
- `FAILED` means the tool could not produce a reliable result. The error and trace ID help technical support find the problem.

## Recommended intake routine

1. Confirm the intake name or number and the source type.
2. Read the five-sentence summary, then check the urgency result.
3. Review every `NOT FOUND` item and every human-review reason.
4. Compare important facts with their evidence quotations.
5. Collect missing information through the firm's approved process.
6. Send the reviewed record to the responsible attorney.

## When to trust it - and when not to

Use the result as an organized first draft when accepted facts have matching evidence and no warning is unexplained. Do not rely on it when names conflict, a quotation appears connected to the wrong person, important information is missing, the source contains instructions aimed at the AI, or the result conflicts with the original submission.

When in doubt, keep the original submission unchanged and ask a person to review it. Never fill a blank by guessing.

## When something breaks

Keep the original submission. Copy the intake ID, trace ID, error message, and the time the problem occurred. Tell the firm's automation or technical-support owner. If the submission may be urgent, also notify the responsible attorney through the firm's normal urgent-intake process; do not wait for the tool to recover.
