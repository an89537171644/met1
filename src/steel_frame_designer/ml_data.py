"""ML dataset data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MLCase(BaseModel):
    case_id: str = Field(min_length=1)
    span_m: float = Field(gt=0)
    eave_height_m: float = Field(gt=0)
    ridge_height_m: float = Field(gt=0)
    frame_spacing_m: float = Field(gt=0)
    target_section_id: str = Field(min_length=1)
    target_mass_kg_m: float | None = Field(default=None, gt=0)
    max_utilization_percent: float | None = Field(default=None, ge=0)
