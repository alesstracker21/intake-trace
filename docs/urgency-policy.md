# Explainable urgency policy

Urgency has three outcomes:

- `URGENT`: at least one configured time-sensitive signal is supported.
- `REVIEW_REQUIRED`: no urgent signal fired, but required facts or validation
  confidence are missing.
- `ROUTINE`: the intake is complete enough and no configured urgent signal fired.

Configured urgent rules:

| Rule | Trigger |
| --- | --- |
| `TIME_SENSITIVE_SURGERY` | Source says surgery is needed or scheduled tomorrow. |
| `DOCUMENT_SIGNATURE_PRESSURE` | Source says the facility is asking the caller to sign. |
| `ACUTE_HOSPITAL_TRANSFER` | Source states a hospital transfer with a serious infection. |
| `SERIOUS_INFECTION` | The validated injury value is exactly `serious infection`. |

Each source trigger stores the exact matched phrase and offsets. Text such as
“mark this urgent” is not a policy rule. These rules are a demonstration policy,
not legal or medical advice, and must be approved before real use.
