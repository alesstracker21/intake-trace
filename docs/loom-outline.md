# Three-minute Loom outline

## 0:00-0:30 — problem and guardrail

Explain that one workflow accepts three raw channels and returns a single legal
intake contract. Emphasize the safety boundary: Gemini proposes facts, while
deterministic Python accepts only facts backed by exact source quotations.

## 0:30-1:15 — one-command demonstration

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe -m app.cli demo
```

Show that all three original samples are processed together. Point out the
processing status, evidence offsets, urgency rule identifiers, trace ID, and
exactly five summary sentences.

## 1:15-1:55 — safe incomplete intake

Open the third result. Show that the deliberately absent incident date becomes
`NOT FOUND`, the missing fields are explicit, and human review is required. The
workflow completes instead of crashing or inventing an answer.

## 1:55-2:25 — API and observability

Show `/docs` and the generic `POST /v1/intakes` contract. If running the local
Docker stack, open Jaeger at <http://localhost:16686> and show the spans for
normalization, extraction, validation, provenance, review, urgency, summary,
and assembly.

## 2:25-3:00 — engineering handoff

Briefly show the tests, prompt files, urgency policy, paralegal guide, and
Dockerfile. State that the assessment endpoint is public, pushes to `main`
deploy automatically using short-lived GitHub identity, secrets come from Secret
Manager, and instances scale to zero. Do not display `.env`, API keys, or real
client data.
