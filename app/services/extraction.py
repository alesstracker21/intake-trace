from __future__ import annotations

from app.models import IntakeProposal, NormalizedIntake
from app.services.agent_runtime import run_structured_agent


class ExtractionService:
    def __init__(self, agent) -> None:
        self._agent = agent

    async def propose(self, intake: NormalizedIntake, trace_id: str) -> tuple[IntakeProposal, int]:
        raw, event_count = await run_structured_agent(
            self._agent,
            output_key="intake_proposal",
            message_text=intake.source_text,
            correlation_id=f"extract-{trace_id}",
        )
        return IntakeProposal.model_validate(raw), event_count
