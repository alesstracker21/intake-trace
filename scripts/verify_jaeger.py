from __future__ import annotations

import argparse
import json
from urllib.parse import urlencode
from urllib.request import urlopen


REQUIRED_SPANS = {
    "intake.processing",
    "intake.normalization",
    "intake.ai_extraction",
    "intake.evidence_validation",
    "intake.provenance_audit",
    "intake.adversarial_review",
    "intake.urgency_assessment",
    "intake.summary_creation",
    "intake.output_assembly",
}
SENSITIVE_MARKERS = {
    "arun desai",
    "camille turner",
    "eleanor watkins",
    "312-555-0148",
    "camille.turner@example.test",
    "michael.chen@chen-soto.example.test",
    '"source_text"',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify IntakeTrace spans in Jaeger.")
    parser.add_argument("--api", default="http://localhost:16686/api")
    parser.add_argument("--service", default="intake-trace")
    return parser.parse_args()


def get_json(url: str) -> dict:
    with urlopen(url, timeout=5) as response:
        return json.load(response)


def main() -> None:
    args = parse_args()
    services = get_json(f"{args.api}/services")["data"]
    if args.service not in services:
        raise SystemExit(f"Service {args.service!r} was not found in Jaeger.")
    query = urlencode({"service": args.service, "limit": 20, "operation": "intake.processing"})
    traces = get_json(f"{args.api}/traces?{query}")["data"]
    operations = {
        span["operationName"] for trace_data in traces for span in trace_data.get("spans", [])
    }
    serialized = json.dumps(traces).casefold()
    report = {
        "trace_count": len(traces),
        "missing_required_spans": sorted(REQUIRED_SPANS - operations),
        "sensitive_content_found": sorted(
            marker for marker in SENSITIVE_MARKERS if marker in serialized
        ),
    }
    print(json.dumps(report, indent=2))
    if report["missing_required_spans"] or report["sensitive_content_found"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
