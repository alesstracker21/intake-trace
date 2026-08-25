from __future__ import annotations

import json

from app.agents.factory import create_extraction_agent
from app.config import Settings
from app.models import IntakeProposal


def test_extractor_uses_configured_model_and_schema(tmp_path):
    settings = Settings(gemini_model="gemini-test-model", output_dir=tmp_path)
    agent = create_extraction_agent(settings)

    assert agent.model == "gemini-test-model"
    assert agent.output_schema is IntakeProposal
    assert agent.output_key == "intake_proposal"
    assert agent.include_contents == "none"
    assert agent.generate_content_config.automatic_function_calling.disable is True


def test_gemini_schema_avoids_additional_properties():
    assert "additionalProperties" not in json.dumps(IntakeProposal.model_json_schema())
