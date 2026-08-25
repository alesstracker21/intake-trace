from __future__ import annotations

import os
from pathlib import Path

# ADK legacy spans otherwise capture prompts and responses by default. Set both
# controls before importing ADK so intake content is not exported accidentally.
os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "")
os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", "FALSE")

from google.adk import Agent  # noqa: E402
from google.genai import types  # noqa: E402

from app.config import Settings  # noqa: E402
from app.models import IntakeProposal  # noqa: E402


PROMPT_ROOT = Path(__file__).resolve().parents[2] / "prompts"


def create_extraction_agent(settings: Settings) -> Agent:
    return Agent(
        name="intake_extractor",
        model=settings.gemini_model,
        description="Proposes intake facts and verbatim evidence for deterministic review.",
        instruction=(PROMPT_ROOT / "extraction.md").read_text(encoding="utf-8"),
        output_schema=IntakeProposal,
        output_key="intake_proposal",
        include_contents="none",
        generate_content_config=types.GenerateContentConfig(
            max_output_tokens=4096,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
