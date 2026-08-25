# API request examples

Start the service on port 8000, then use these PowerShell examples from the
repository root.

## Voicemail transcript

```powershell
$request = @{
  intake_id = "INT-SYNTH-001"
  channel = "voicemail"
  payload = Get-Content -Raw .\samples\01_voicemail_transcript.txt
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/intakes `
  -ContentType application/json -Body $request
```

The payload is already a transcript. Speech-to-text is intentionally outside
the workflow.

## Web-form JSON

```powershell
$form = Get-Content -Raw .\samples\02_web_form_submission.json | ConvertFrom-Json
$request = @{
  intake_id = "INT-SYNTH-002"
  channel = "web_form"
  payload = $form
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/intakes `
  -ContentType application/json -Body $request
```

## RFC 822 referral email

```powershell
$request = @{
  intake_id = "INT-SYNTH-003"
  channel = "referral_email"
  payload = Get-Content -Raw .\samples\03_referral_email.eml
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/intakes `
  -ContentType application/json -Body $request
```

Malformed request bodies return HTTP 422. A raw payload that does not match its
selected channel returns a canonical failure envelope with HTTP 400. Retryable
model failures return HTTP 502; non-retryable internal integrity failures return
HTTP 500. Missing facts are a completed HTTP 200 result, not an error.
