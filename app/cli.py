from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from app.api.dependencies import get_pipeline
from app.config import PROJECT_ROOT, get_settings
from app.models import IntakeRequest


SAMPLES = PROJECT_ROOT / "samples"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the IntakeTrace workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Process all three included raw samples.")
    demo.add_argument("--output-dir", type=Path, default=None)
    demo.add_argument("--no-write", action="store_true", help="Print results without saving files.")
    subparsers.add_parser("check", help="Validate local configuration without model calls.")
    return parser.parse_args()


def sample_requests() -> list[IntakeRequest]:
    return [
        IntakeRequest(
            intake_id="INT-SYNTH-001",
            channel="voicemail",
            payload=(SAMPLES / "01_voicemail_transcript.txt").read_text(encoding="utf-8"),
        ),
        IntakeRequest(
            intake_id="INT-SYNTH-002",
            channel="web_form",
            payload=json.loads(
                (SAMPLES / "02_web_form_submission.json").read_text(encoding="utf-8")
            ),
        ),
        IntakeRequest(
            intake_id="INT-SYNTH-003",
            channel="referral_email",
            payload=(SAMPLES / "03_referral_email.eml").read_text(encoding="utf-8"),
        ),
    ]


async def run_demo(output_dir: Path | None, no_write: bool) -> int:
    if not os.getenv("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY is not set. Copy .env.example to .env and add a valid key.")
        return 2
    pipeline = get_pipeline()
    target = output_dir or get_settings().output_dir
    if not no_write:
        target.mkdir(parents=True, exist_ok=True)

    failed = False
    for request in sample_requests():
        result = await pipeline.process(request)
        document = result.model_dump(mode="json")
        print(json.dumps(document, indent=2, ensure_ascii=False))
        if not no_write:
            path = target / f"{result.intake_id.lower()}.json"
            path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"WROTE {path}")
        failed = failed or result.processing_status == "FAILED"
    return 1 if failed else 0


def check_configuration() -> int:
    settings = get_settings()
    requests = sample_requests()
    print("Configuration is valid; no API call was made.")
    print(f"Model: {settings.gemini_model}")
    print(f"Review model: {settings.gemini_review_model}")
    print(f"Samples: {len(requests)}")
    return 0


def main() -> None:
    args = parse_args()
    if args.command == "check":
        raise SystemExit(check_configuration())
    raise SystemExit(asyncio.run(run_demo(args.output_dir, args.no_write)))


if __name__ == "__main__":
    main()
