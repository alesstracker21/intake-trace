from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.facts import Evidence


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UrgencyResult(StrictModel):
    flag: Literal["URGENT", "ROUTINE", "REVIEW_REQUIRED"]
    reason: str = Field(min_length=1)
    rule_ids: list[str]
    evidence: list[Evidence]


class SummaryProvenance(StrictModel):
    sentence: int = Field(ge=1, le=5)
    fact_paths: list[str]


class AttorneySummary(StrictModel):
    sentences: list[str] = Field(min_length=5, max_length=5)
    provenance: list[SummaryProvenance] = Field(min_length=5, max_length=5)
