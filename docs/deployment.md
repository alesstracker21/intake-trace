# Deployment

## Current Cloud Run deployment

The application is deployed in a dedicated Google Cloud project, separate from
existing workloads:

- Project: `intake-trace-20260824-a89542`
- Region: `us-central1`
- Service: `intake-trace`
- Revision: `intake-trace-00001-6g5`
- URL: <https://intake-trace-sqkre4xmpa-uc.a.run.app>
- Access: authenticated callers only
- Scaling: zero to one instance
- Runtime identity: dedicated `intake-trace-runtime` service account

The Gemini key is stored in Google Secret Manager and injected as an environment
variable. It is not part of the image, repository, deployment command, or
application logs. The first live verification covered both `GET /health` and the
complete third intake: it returned `COMPLETED`, `NOT FOUND` for the absent date,
the expected missing-field list, required human review, five summary sentences,
and a trace ID.

To verify health with the currently signed-in Google account:

```powershell
$url = gcloud run services describe intake-trace `
  --project intake-trace-20260824-a89542 `
  --region us-central1 `
  --format="value(status.url)"
$token = gcloud auth print-identity-token
Invoke-RestMethod -Uri "$url/health" `
  -Headers @{ Authorization = "Bearer $token" }
```

Keep the service private unless public access is a deliberate product decision.
For a production launch, add caller authentication, rate limits, budget alerts,
retention rules, and a managed OTLP destination before increasing the maximum
instance count.

## Local Docker

The root `Dockerfile` runs as a non-root user and honors the platform-provided
`PORT`. For the API plus local Jaeger:

```powershell
$env:GOOGLE_API_KEY = "your-key"
docker compose up --build
```

The API is available at <http://localhost:8000> and Jaeger at
<http://localhost:16686>.

## Railway path

Railway can build the same root Dockerfile. Configure `GOOGLE_API_KEY` as a
Railway secret and set the documented environment variables from `.env.example`.
No database, volume, or Redis service is required for this assessment. Any
demonstration JSON written to `outputs/` is ephemeral on Railway and Cloud Run;
use managed object storage or a database if persistence becomes a requirement.

Repository-driven deployment can be added later as a separate CI/CD change.
That workflow should use workload identity or another short-lived credential,
run tests before deployment, and avoid storing a long-lived cloud key in GitHub.
