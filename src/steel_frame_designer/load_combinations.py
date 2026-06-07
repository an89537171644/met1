"""Load-combination data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoadCombinationTerm(BaseModel):
    load_id: str = Field(min_length=1)
    factor: float | None = Field(default=None, gt=0)
    role: str = "accompanying"


class LoadCombination(BaseModel):
    combo_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    limit_state: str = Field(min_length=1)
    combination_type: str = "main"
    leading_load_id: str | None = None
    terms: list[LoadCombinationTerm] = Field(default_factory=list)
    source_norm: str = "SP 20.13330.2016"
    description: str = ""
