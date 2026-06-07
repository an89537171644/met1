"""Section catalog models and CSV loading helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SectionProfile(BaseModel):
    section_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    standard: str = ""
    mark: str = ""
    mass_kg_m: float | None = None
    A_cm2: float | None = None
    Ix_cm4: float | None = None
    Iy_cm4: float | None = None
    Wx_cm3: float | None = None
    Wy_cm3: float | None = None
    ix_cm: float | None = None
    iy_cm: float | None = None
    h_mm: float | None = None
    b_mm: float | None = None
    tw_mm: float | None = None
    tf_mm: float | None = None
    notes: str = ""

    @field_validator(
        "mass_kg_m",
        "A_cm2",
        "Ix_cm4",
        "Iy_cm4",
        "Wx_cm3",
        "Wy_cm3",
        "ix_cm",
        "iy_cm",
        "h_mm",
        "b_mm",
        "tw_mm",
        "tf_mm",
        mode="before",
    )
    @classmethod
    def blank_numeric_as_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


def load_section_catalog(path: str | Path) -> list[SectionProfile]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        return [SectionProfile.model_validate(row) for row in csv.DictReader(file)]
