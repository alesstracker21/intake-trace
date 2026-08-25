from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Channel(StrEnum):
    VOICEMAIL = "voicemail"
    WEB_FORM = "web_form"
    REFERRAL_EMAIL = "referral_email"


class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Channel
    provider: str = Field(min_length=1)
    external_id: str = Field(min_length=1)
    received_at: datetime


class NormalizedIntake(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intake_id: str = Field(min_length=1)
    source: SourceMetadata
    source_text: str = Field(min_length=1)

    @field_validator("intake_id", "source_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value
