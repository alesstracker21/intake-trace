# IntakeTrace

IntakeTrace turns voicemail transcripts, web-form submissions, and referral
emails into evidence-backed legal-intake JSON. Gemini proposes facts through a
Google ADK agent; deterministic Python code decides what is accepted, routes
urgency, and creates an exactly five-sentence attorney summary.

## What is included

- `POST /v1/intakes` for all three raw channels and `GET /health`.
- Separate channel adapters and one normalized intake contract.
- Schema-constrained ADK extraction using configurable Gemini models.
- Exact quote validation with Python-computed character offsets.
- An independent provenance audit and adversarial ADK reviewer.
- Explainable urgency rules and deterministic summaries.
- Safe completed and failed response envelopes with OpenTelemetry trace IDs.
- A single three-sample demonstration command.
- Docker packaging and an optional local Jaeger trace viewer.

## Local setup

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder `GOOGLE_API_KEY`. Never commit or show
that file in a recording. `GEMINI_MODEL` and `GEMINI_REVIEW_MODEL` default to
`gemini-3.7-flash`.

Verify local imports, models, and samples without making a model call:

```powershell
.\.venv\Scripts\python.exe -m app.cli check
.\.venv\Scripts\python.exe -m pytest
```

## Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Health: <http://localhost:8000/health>
- Interactive API documentation: <http://localhost:8000/docs>

The generic request contract is:

```json
{
  "intake_id": "optional caller-supplied identifier",
  "channel": "voicemail | web_form | referral_email",
  "payload": "raw text or the raw form object"
}
```

Copy-ready requests for all channels are in [docs/api-examples.md](docs/api-examples.md).

## Run the complete demonstration

This is the recommended Loom command. It processes all three samples from their
original formats, prints each canonical result, and writes JSON to `outputs/`.

```powershell
.\.venv\Scripts\python.exe -m app.cli demo
```

Intake #3 completes with `NOT FOUND` values, an explicit missing-field list,
and required human review; it is not treated as a technical failure.

## Run with Docker and Jaeger

Export `GOOGLE_API_KEY` in the terminal, then start both services:

```powershell
$env:GOOGLE_API_KEY = "your-key"
docker compose up --build
```

The API is at <http://localhost:8000> and Jaeger is at
<http://localhost:16686>. Select service `intake-trace` after processing an
intake. Stop the stack with `docker compose down`.

The application never adds prompts, source text, model responses, or contact
details to custom span attributes. Both ADK message-content capture controls are
disabled before ADK is imported.

## Design documents

- [Architecture and safety boundary](docs/architecture.md)
- [Evidence-validation rule](docs/evidence-validation.md)
- [Urgency policy](docs/urgency-policy.md)
- [API examples](docs/api-examples.md)
- [Paralegal enablement guide](docs/paralegal-enablement.md)
- [Three-minute Loom outline](docs/loom-outline.md)
- [Deployment options](docs/deployment.md)

## Deployment status

The application is deployed publicly to Google Cloud Run in the dedicated
`intake-trace-20260824-a89542` project. The root `Dockerfile` also listens on
Railway's injected `PORT`, so the same image can be deployed there later without
changing application code. Pushes to `main` run tests, build the image, deploy
the revision, and verify the public health endpoint. See
[docs/deployment.md](docs/deployment.md) for details. Local files under
`outputs/` are ephemeral on either platform and are not a persistence strategy.
