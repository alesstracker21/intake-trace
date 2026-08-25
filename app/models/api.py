from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.intake import Channel


class IntakeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "intake_id": "INT-SYNTH-001",
                    "channel": "voicemail",
                    "payload": "VOICEMAIL TRANSCRIPT\nCall ID: CALL-001\nReceived at: 2026-08-18T15:42:00-05:00\n\nTranscript text...",
                },
                {
                    "intake_id": "INT-SYNTH-002",
                    "channel": "web_form",
                    "payload": {
                        "submission_id": "FORM-001",
                        "submitted_at": "2026-08-20T10:15:00-05:00",
                        "provider": "generic_webhook",
                        "fields": {"potential_client_name": "Camille Turner"},
                    },
                },
                {
                    "intake_id": "INT-SYNTH-003",
                    "channel": "referral_email",
                    "payload": "From: Attorney <attorney@example.test>\nSubject: Referral\nDate: Fri, 21 Aug 2026 16:20:00 -0500\nMessage-ID: <ref-1@example.test>\n\nEmail body...",
                },
            ]
        },
    )

    intake_id: str | None = Field(default=None, min_length=1, max_length=100)
    channel: Channel
    payload: str | dict[str, Any]

    @model_validator(mode="after")
    def payload_matches_channel(self) -> "IntakeRequest":
        if self.channel == Channel.WEB_FORM and not isinstance(self.payload, dict):
            raise ValueError("web_form payload must be a JSON object")
        if self.channel != Channel.WEB_FORM and not isinstance(self.payload, str):
            raise ValueError(f"{self.channel.value} payload must be a string")
        return self


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model: str
