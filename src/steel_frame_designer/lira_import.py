"""CSV import and validation helpers for LIRA exports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator


LIRA_ELEMENT_FORCE_COLUMNS = {
    "case_id",
    "combo_id",
    "element_id",
    "element_role",
    "station_rel",
    "N_kN",
    "Qy_kN",
    "Mz_kNm",
    "ux_mm",
    "uy_mm",
    "rz_rad",
    "utilization_percent",
    "check_name",
}


class CSVValidationIssue(BaseModel):
    code: str
    message: str
    row_number: int | None = None
    column: str | None = None


class CSVValidationReport(BaseModel):
    path: str
    row_count: int
    issues: list[CSVValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


class LiraImportRecord(BaseModel):
    case_id: str
    lira_model_file: str
    lira_version: str = ""
    run_date: str = ""
    norm_sp16_edition: str = ""
    norm_sp20_edition: str = ""
    export_files: str = ""
    model_hash: str = ""
    success: bool = False
    notes: str = ""

    @field_validator("success", mode="before")
    @classmethod
    def parse_success(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return value


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def validate_required_columns(rows: list[dict[str, str]], required: set[str]) -> list[CSVValidationIssue]:
    if not rows:
        return [CSVValidationIssue(code="empty_csv", message="CSV file is empty")]

    missing = sorted(required.difference(rows[0].keys()))
    return [
        CSVValidationIssue(
            code="missing_column",
            message=f"Missing required column: {column}",
            column=column,
        )
        for column in missing
    ]


def validate_blank_cells(
    rows: list[dict[str, str]],
    columns: set[str],
) -> list[CSVValidationIssue]:
    issues: list[CSVValidationIssue] = []
    for row_number, row in enumerate(rows, start=2):
        for column in sorted(columns):
            if column in row and not str(row[column]).strip():
                issues.append(
                    CSVValidationIssue(
                        code="blank_cell",
                        message=f"Blank value in required data column: {column}",
                        row_number=row_number,
                        column=column,
                    )
                )
    return issues


def validate_lira_element_forces(path: str | Path) -> CSVValidationReport:
    rows = read_csv_rows(path)
    issues = validate_required_columns(rows, LIRA_ELEMENT_FORCE_COLUMNS)
    if not issues:
        issues.extend(
            validate_blank_cells(
                rows,
                {
                    "case_id",
                    "combo_id",
                    "element_id",
                    "element_role",
                    "station_rel",
                    "N_kN",
                    "Qy_kN",
                    "Mz_kNm",
                    "ux_mm",
                    "uy_mm",
                    "utilization_percent",
                    "check_name",
                },
            )
        )
    return CSVValidationReport(path=str(path), row_count=len(rows), issues=issues)


def import_lira_forces(path: str | Path) -> list[dict[str, str]]:
    rows = read_csv_rows(path)
    issues = validate_required_columns(rows, LIRA_ELEMENT_FORCE_COLUMNS)
    if issues:
        message = "; ".join(issue.message for issue in issues)
        raise ValueError(message)
    return rows
