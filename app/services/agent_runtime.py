from __future__ import annotations

import json
import uuid
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types


async def run_structured_agent(
    agent: Any,
    *,
    output_key: str,
    message_text: str,
    correlation_id: str,
) -> tuple[Any, int]:
    """Run one stateless ADK invocation and return its schema-validated state."""

    app_name = f"intake_trace_{agent.name}"
    runner = InMemoryRunner(agent=agent, app_name=app_name)
    session_id = f"{correlation_id}-{uuid.uuid4().hex[:12]}"
    session = await runner.session_service.create_session(
        app_name=app_name,
        user_id="intake_workflow",
        session_id=session_id,
    )

    event_count = 0
    async for _ in runner.run_async(
        user_id="intake_workflow",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text=message_text)],
        ),
    ):
        event_count += 1

    completed = await runner.session_service.get_session(
        app_name=app_name,
        user_id="intake_workflow",
        session_id=session.id,
    )
    if completed is None or output_key not in completed.state:
        raise RuntimeError(f"{agent.name} produced no structured result")

    raw = completed.state[output_key]
    return (json.loads(raw) if isinstance(raw, str) else raw), event_count
