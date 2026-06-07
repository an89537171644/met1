"""Material data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SteelMaterial(BaseModel):
    steel_grade: str = Field(min_length=1)
    source: str = "user_catalog_or_sp16_material_table"
