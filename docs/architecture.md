# Architecture and safety boundary

```text
raw request
  -> channel adapter
  -> normalized source text
  -> ADK extraction proposal
  -> deterministic evidence validation
  -> independent provenance audit
  -> adversarial ADK review
  -> deterministic urgency policy
  -> deterministic five-sentence summary
  -> canonical response envelope
```

The two model calls are advisory. The extractor proposes values and verbatim
quotes. Python locates each quote, computes offsets, confirms the proposed value
occurs inside its cited text, rejects malformed items, and converts unsupported
scalar facts to `NOT FOUND`. The independent provenance audit then checks that
every stored `source_text[start:end]` slice still equals its quote.

The reviewer may escalate a result but cannot restore a rejected fact or clear
missing information. A small deterministic detector also recognizes explicit
instruction-override phrases. This does not claim to detect every possible
attack; it guarantees that recognized signals and AI concerns require review.

Urgency is ordinary Python policy. Narrow source phrases and validated injury
facts trigger named rules with exact evidence. An urgent signal takes precedence
over missing information so an incomplete but time-sensitive matter is not
quietly downgraded.

The summary is a template over validated facts and urgency results. It cannot
introduce a new model claim and always returns five sentences. Sentence-level
fact paths are retained separately.

The FastAPI and CLI interfaces call the same `PipelineService`. A future queue,
database, case-management connector, or cloud entry point can sit outside that
service without moving validation or policy into the transport layer.

## Production path

Before handling real client information, add authentication, authorization,
request-size limits, encryption and retention controls, persistent audit
storage, reviewed urgency policy, model evaluations, rate limiting, and an
approved incident-response owner. The current samples are synthetic.
