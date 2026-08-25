# Deployment

## Current Cloud Run deployment

The application is deployed in a dedicated Google Cloud project, separate from
existing workloads:

- Project: `intake-trace-20260824-a89542`
- Region: `us-central1`
- Service: `intake-trace`
- Revision: `intake-trace-00001-6g5`
- URL: <https://intake-trace-sqkre4xmpa-uc.a.run.app>
- Access: public; no caller authentication required
- Scaling: zero to one instance
- Runtime identity: dedicated `intake-trace-runtime` service account

The Gemini key is stored in Google Secret Manager and injected as an environment
variable. It is not part of the image, repository, deployment command, or
application logs. The first live verification covered both `GET /health` and the
complete third intake: it returned `COMPLETED`, `NOT FOUND` for the absent date,
the expected missing-field list, required human review, five summary sentences,
and a trace ID.

To verify health without credentials:

```powershell
Invoke-RestMethod -Uri `
  "https://intake-trace-sqkre4xmpa-uc.a.run.app/health"
```

Because the assessment endpoint is public, the service remains capped at one
instance and scales to zero. Before handling real client data, add caller
authentication, rate limits, budget alerts, retention rules, and a managed OTLP
destination.

## Deployment on repository push

Every push to `main` runs `.github/workflows/deploy-cloud-run.yml`. The workflow:

1. installs the application and runs all tests;
2. exchanges GitHub's short-lived OIDC token for a repository-scoped Google
   identity;
3. builds the Docker image with Cloud Build;
4. deploys the new public Cloud Run revision; and
5. calls `/health` without credentials.

The Google identity accepts tokens only from the
`alesstracker21/intake-trace` repository's `main` branch. No service-account key
or API key is stored in GitHub. The runtime reads the Gemini key from Secret
Manager.

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

The same Dockerfile remains suitable for a later Railway deployment.
