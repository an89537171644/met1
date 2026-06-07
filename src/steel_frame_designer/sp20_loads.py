"""SP 20 load-case data structures."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class LoadGroup(StrEnum):
    PERMANENT = "permanent"
    SNOW = "snow"
    WIND = "wind"
    ROOF_LIVE = "roof_live"
    TEMPERATURE = "temperature"
    CRANE = "crane"
    ICE = "ice"
    SPECIAL = "special"


class SP20LoadCase(BaseModel):
    case_id: str = "template"
    load_id: str = Field(min_length=1)
    group: LoadGroup
    subtype: str = ""
    scheme: str = ""
    direction: str = ""
    value: float | None = None
    unit: str = ""
    tributary_width_m: float | None = Field(default=None, gt=0)
    gamma_f: float | None = Field(default=None, gt=0)
    duration_type: str = ""
    source_norm: str = "SP 20.13330.2016"
    notes: str = ""


def build_minimal_load_cases(case_id: str = "template", tributary_width_m: float | None = None) -> list[SP20LoadCase]:
    return [
        SP20LoadCase(
            case_id=case_id,
            load_id="G_self_weight",
            group=LoadGroup.PERMANENT,
            subtype="steel_frame",
            scheme="auto_from_section",
            direction="gravity",
            unit="auto",
            tributary_width_m=tributary_width_m,
            duration_type="permanent",
            notes="Computed from selected section mass.",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="G_roof_dead",
            group=LoadGroup.PERMANENT,
            subtype="roof_dead",
            scheme="uniform_on_roof",
            direction="gravity",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="permanent",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="S_symmetric",
            group=LoadGroup.SNOW,
            subtype="gable_roof",
            scheme="symmetric",
            direction="gravity",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="S_left_unbalanced",
            group=LoadGroup.SNOW,
            subtype="gable_roof",
            scheme="left_unbalanced",
            direction="gravity",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="S_right_unbalanced",
            group=LoadGroup.SNOW,
            subtype="gable_roof",
            scheme="right_unbalanced",
            direction="gravity",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="W_plus_x",
            group=LoadGroup.WIND,
            subtype="external_internal",
            scheme="plus_x",
            direction="+X",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="W_minus_x",
            group=LoadGroup.WIND,
            subtype="external_internal",
            scheme="minus_x",
            direction="-X",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
        SP20LoadCase(
            case_id=case_id,
            load_id="Q_roof_maintenance",
            group=LoadGroup.ROOF_LIVE,
            subtype="maintenance",
            scheme="uniform_on_roof",
            direction="gravity",
            unit="kPa",
            tributary_width_m=tributary_width_m,
            duration_type="short_term",
        ),
    ]
