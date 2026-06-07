"""SP 20 load-case data structures."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LoadGroup(StrEnum):
    PERMANENT = "permanent"
    SNOW = "snow"
    WIND = "wind"
    ROOF_LIVE = "roof_live"
    TEMPERATURE = "temperature"
    CRANE = "crane"
    ICE = "ice"
    SPECIAL = "special"


SUPPORTED_LOAD_UNITS = {
    "auto",
    "kPa",
    "kN",
    "kN/m",
    "kN/m2",
    "kg/m",
    "kg/m2",
}


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

    @field_validator("value", "tributary_width_m", "gamma_f", mode="before")
    @classmethod
    def blank_numeric_as_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    @property
    def value_is_auto_computed(self) -> bool:
        return self.unit == "auto" or self.scheme == "auto_from_section"


class LoadFactorReference(BaseModel):
    """A load factor from configuration or a normative reference table."""

    load_id: str = Field(min_length=1)
    gamma_f: float = Field(gt=0)
    source_norm: str = Field(min_length=1)
    source_note: str = ""


class LoadCaseValidationIssue(BaseModel):
    code: str
    load_id: str
    field: str
    message: str


class LoadCaseValidationReport(BaseModel):
    issues: list[LoadCaseValidationIssue] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def apply_load_factors(
    load_cases: list[SP20LoadCase],
    factor_table: list[LoadFactorReference],
) -> list[SP20LoadCase]:
    """Apply gamma_f values only from caller-supplied configuration/table data."""
    factors_by_load_id = {factor.load_id: factor for factor in factor_table}
    updated_cases: list[SP20LoadCase] = []
    for load_case in load_cases:
        factor = factors_by_load_id.get(load_case.load_id)
        if factor is None:
            updated_cases.append(load_case)
            continue
        updated_cases.append(
            load_case.model_copy(
                update={
                    "gamma_f": factor.gamma_f,
                    "source_norm": factor.source_norm,
                    "notes": _append_note(load_case.notes, factor.source_note),
                }
            )
        )
    return updated_cases


def validate_load_cases(
    load_cases: list[SP20LoadCase],
    *,
    require_values: bool = True,
    require_factors: bool = True,
) -> LoadCaseValidationReport:
    issues: list[LoadCaseValidationIssue] = []
    seen_load_ids: set[str] = set()
    for load_case in load_cases:
        if load_case.load_id in seen_load_ids:
            issues.append(
                LoadCaseValidationIssue(
                    code="duplicate_load_id",
                    load_id=load_case.load_id,
                    field="load_id",
                    message="Load id must be unique within a load-case set.",
                )
            )
        seen_load_ids.add(load_case.load_id)

        _require_text(issues, load_case, "subtype", load_case.subtype)
        _require_text(issues, load_case, "scheme", load_case.scheme)
        _require_text(issues, load_case, "direction", load_case.direction)
        _require_text(issues, load_case, "unit", load_case.unit)
        _require_text(issues, load_case, "duration_type", load_case.duration_type)
        _require_text(issues, load_case, "source_norm", load_case.source_norm)

        if load_case.unit and load_case.unit not in SUPPORTED_LOAD_UNITS:
            issues.append(
                LoadCaseValidationIssue(
                    code="unsupported_unit",
                    load_id=load_case.load_id,
                    field="unit",
                    message=f"Unsupported load unit: {load_case.unit}",
                )
            )

        if load_case.tributary_width_m is None:
            issues.append(
                LoadCaseValidationIssue(
                    code="missing_tributary_width",
                    load_id=load_case.load_id,
                    field="tributary_width_m",
                    message="Tributary width is required to convert surface loads to frame loads.",
                )
            )

        if require_values and load_case.value is None and not load_case.value_is_auto_computed:
            issues.append(
                LoadCaseValidationIssue(
                    code="missing_value",
                    load_id=load_case.load_id,
                    field="value",
                    message="Load value is required unless the load is computed automatically.",
                )
            )

        if require_factors and load_case.gamma_f is None:
            issues.append(
                LoadCaseValidationIssue(
                    code="missing_gamma_f",
                    load_id=load_case.load_id,
                    field="gamma_f",
                    message="Load factor gamma_f must come from configuration or a normative table.",
                )
            )

    return LoadCaseValidationReport(issues=issues)


def load_sp20_load_cases_csv(path: str | Path) -> list[SP20LoadCase]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        return [SP20LoadCase.model_validate(row) for row in csv.DictReader(file)]


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


def _append_note(existing_note: str, new_note: str) -> str:
    if not new_note:
        return existing_note
    if not existing_note:
        return new_note
    return f"{existing_note}; {new_note}"


def _require_text(
    issues: list[LoadCaseValidationIssue],
    load_case: SP20LoadCase,
    field_name: str,
    value: str,
) -> None:
    if value.strip():
        return
    issues.append(
        LoadCaseValidationIssue(
            code="missing_text",
            load_id=load_case.load_id,
            field=field_name,
            message=f"{field_name} must not be empty.",
        )
    )
