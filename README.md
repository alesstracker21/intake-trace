# IntakeTrace

IntakeTrace is an evidence-backed AI intake workflow for legal teams. It accepts a voicemail transcript, web-form submission, or RFC 822 referral email and returns one structured, reviewable JSON record.

- **Live assessment service:** <https://intake-trace-sqkre4xmpa-uc.a.run.app>
- **Interactive API:** <https://intake-trace-sqkre4xmpa-uc.a.run.app/docs>
- **Health check:** <https://intake-trace-sqkre4xmpa-uc.a.run.app/health>

> The public deployment is limited to synthetic assessment data. Authentication, rate limiting, approved retention, and persistent audit storage must be added before processing real client information.

## Assessment requirements

| Requirement | Implementation |
| --- | --- |
| Structured JSON | One canonical response contract for all three channels |
| Attorney-ready summary | Exactly five deterministic sentences built from validated facts |
| Traceability | Every accepted fact includes an exact source quotation and Python-computed offsets |
| Honest missing data | Unsupported facts become `NOT FOUND`; they are never guessed |
| Safe failure | Incomplete intake #3 completes with missing fields and mandatory human review |
| Working demonstration | FastAPI endpoint and one-command three-sample CLI |

## Safety boundary

```text
raw intake
  -> channel adapter
  -> normalized source text
  -> ADK extraction proposal
  -> deterministic evidence validation
  -> independent provenance audit
  -> adversarial ADK review
  -> deterministic urgency rules
  -> deterministic five-sentence summary
  -> canonical JSON response
```

Gemini proposes facts and supporting quotations. Ordinary Python decides whether those facts are accepted. Python locates each quotation in the source, computes its offsets, rejects unsupported claims, and performs a second provenance audit before releasing a result.

The adversarial reviewer can add warnings but cannot restore a rejected fact or clear missing information. Urgency and summary construction are deterministic so important routing and handoff language remain explainable.

## API contract

All channels use one endpoint:

```http
POST /v1/intakes
Content-Type: application/json
```

```json
{
  "intake_id": "optional-caller-id",
  "channel": "voicemail | web_form | referral_email",
  "payload": "raw text, or a raw JSON object for web_form"
}
```

The API returns `COMPLETED` for a safely processed intake even when facts are missing. Malformed requests and technical failures return stable error envelopes with a trace ID. Copy-ready requests for all channels are in [docs/api-examples.md](docs/api-examples.md).

## Local setup

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Add a development `GOOGLE_API_KEY` to `.env`. Never commit or display that file. The default extraction and review model is `gemini-3.7-flash`.

Run deterministic checks without making a model call:

```powershell
.\.venv\Scripts\python.exe -m app.cli check
.\.venv\Scripts\python.exe -m pytest -q
```

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000/docs> for the local interactive API.

## Three-intake demonstration

The recommended walkthrough command processes all original sample formats, prints their canonical results, and writes JSON documents to `outputs/`:

```powershell
.\.venv\Scripts\python.exe -m app.cli demo
```

Intake #3 intentionally omits the incident date and direct client contact. The workflow returns `NOT FOUND`, identifies the missing fields, marks the urgent hospital-transfer language, and requires human review instead of inventing an answer or crashing.

## Docker and local traces

Set the key in the current terminal and start the API with Jaeger:

```powershell
$env:GOOGLE_API_KEY = "your-key"
docker compose up --build
```

- API: <http://localhost:8000>
- Interactive API: <http://localhost:8000/docs>
- Jaeger: <http://localhost:16686>

After processing an intake, select the `intake-trace` service in Jaeger. The trace shows normalization, extraction, validation, provenance audit, adversarial review, urgency, summary, and assembly. Custom trace attributes exclude prompts, source text, model responses, contact details, and credentials.

## Deployment

The application runs on Google Cloud Run in an isolated assessment project. Pushes to `main` run the test suite, build the non-root container, deploy a new revision, and verify `/health`. GitHub authenticates to Google Cloud with short-lived OIDC credentials; the Gemini key is read from Secret Manager rather than GitHub or the image.

The same Dockerfile honors a platform-provided `PORT` and can run on Railway. Demonstration files under `outputs/` are ephemeral in cloud containers and are not durable storage. See [docs/deployment.md](docs/deployment.md) for the deployment boundary and production-hardening requirements.

## Design decision and tradeoff

The central design decision is to separate AI extraction from deterministic acceptance. This gives up some flexibility, because a correct paraphrase without exact evidence may be rejected, but it creates a clear rule a reviewer can inspect: no accepted fact without source support.

A second ADK reviewer provides defense in depth and prompt-injection detection, at the cost of another model call, additional latency, and additional token usage. In a higher-volume version, the same deterministic test fixtures and service boundaries can support prompt/model evaluations or route only uncertain cases through the second reviewer.

## Repository guide

- `app/adapters/` - raw-channel normalization
- `app/agents/` and `prompts/` - version-controlled ADK behavior
- `app/services/` - validation, review, urgency, summary, and orchestration
- `app/api/` - FastAPI transport
- `tests/` - deterministic unit, safety, API, and end-to-end tests
- `samples/` - synthetic assessment inputs
- `docs/` - architecture, policies, deployment, API, and enablement material

Key documents:

- [Architecture and safety boundary](docs/architecture.md)
- [Evidence enforcement rule](docs/evidence-validation.md)
- [Urgency policy](docs/urgency-policy.md)
- [API examples](docs/api-examples.md)
- [Paralegal enablement guide](docs/paralegal-enablement.pdf)
- [Three-minute walkthrough](docs/loom-outline.md)
- [Deployment](docs/deployment.md)

Regenerate the one-page PDF after editing its Markdown source:

```powershell
.\.venv\Scripts\python.exe scripts\build_paralegal_pdf.py
```
