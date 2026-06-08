"""Demo end-to-end pipeline for the sample gable frame case."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig, load_config, validate_config
from .lira_import import import_lira_forces, read_csv_rows, validate_lira_element_forces
from .ml_model import FrequencySectionRecommender
from .reports import write_markdown_report
from .sections import SectionProfile, load_section_catalog
from .sp20_loads import SP20LoadCase


DEMO_STEPS = (
    "validate-input",
    "build-loads",
    "import-lira",
    "build-dataset",
    "train",
    "predict",
    "verify",
    "report",
)

DEMO_WARNING_RU = (
    "ML-рекомендация не является нормативным расчётом по СП 16/СП 20. "
    "Для инженерного применения требуется отдельная проверка расчётным модулем или ЛИРА."
)

DEMO_WARNING_EN = (
    "ML recommendation is not a normative calculation under SP 16/SP 20. "
    "Engineering use requires a separate verification module or LIRA check."
)

LOAD_COLUMNS = {
    "case_id",
    "load_id",
    "group",
    "subtype",
    "scheme",
    "direction",
    "value",
    "unit",
    "tributary_width_m",
    "gamma_f",
    "duration_type",
    "source_norm",
    "notes",
}

COMBINATION_COLUMNS = {
    "combo_id",
    "case_id",
    "limit_state",
    "combination_type",
    "leading_load_id",
    "load_id",
    "factor",
    "source_norm",
    "description",
}

LABEL_COLUMNS = {
    "case_id",
    "target_section_id",
    "target_mass_kg_m",
    "max_utilization_percent",
    "governing_combo",
    "governing_element",
    "governing_check",
    "pass_status",
    "notes",
}

DATASET_COLUMNS = [
    "case_id",
    "span_m",
    "eave_height_m",
    "ridge_height_m",
    "roof_slope_deg",
    "frame_spacing_m",
    "building_length_m",
    "frame_count",
    "support_left",
    "support_right",
    "steel_grade",
    "snow_value_kpa",
    "wind_value_kpa",
    "roof_dead_kpa",
    "purlins_kpa",
    "roof_live_kpa",
    "load_case_count",
    "load_combination_count",
    "section_catalog_count",
    "max_abs_n_kN",
    "max_abs_qy_kN",
    "max_abs_mz_kNm",
    "max_abs_uy_mm",
    "target_section_id",
    "target_mass_kg_m",
    "max_utilization_percent",
    "governing_combo",
    "governing_element",
    "governing_check",
    "pass_status",
]

PREDICTION_COLUMNS = [
    "case_id",
    "rank",
    "section_id",
    "mass_kg_m",
    "model_type",
    "verification_status",
    "selected_for_report",
    "verification_note",
]


@dataclass(frozen=True)
class DemoPaths:
    """Concrete input and output paths used by the demo pipeline."""

    output_root: Path
    sample_root: Path
    frame_case: Path
    section_catalog: Path
    sp20_loads: Path
    load_combinations: Path
    lira_forces: Path
    labels: Path
    ml_dataset: Path
    predictions: Path
    report: Path
    model_artifact: Path

    @classmethod
    def build(
        cls,
        frame_case: str | Path = Path("data/samples/frame_case.yaml"),
        sample_root: str | Path = Path("data/samples"),
        output_root: str | Path = Path("."),
    ) -> "DemoPaths":
        sample_root_path = Path(sample_root)
        output_root_path = Path(output_root)
        return cls(
            output_root=output_root_path,
            sample_root=sample_root_path,
            frame_case=Path(frame_case),
            section_catalog=sample_root_path / "section_catalog.csv",
            sp20_loads=sample_root_path / "sp20_loads.csv",
            load_combinations=sample_root_path / "load_combinations.csv",
            lira_forces=sample_root_path / "lira_element_forces.csv",
            labels=sample_root_path / "selected_sections_labels.csv",
            ml_dataset=output_root_path / "data/processed/ml_dataset.csv",
            predictions=output_root_path / "data/output/predictions.csv",
            report=output_root_path / "reports/demo_report.md",
            model_artifact=output_root_path / "artifacts/baseline_model.json",
        )


@dataclass(frozen=True)
class DemoResult:
    """Summary returned after a successful demo run."""

    paths: DemoPaths
    steps: tuple[str, ...]
    selected_section_id: str
    output_files: tuple[Path, ...]


def run_demo(
    frame_case: str | Path = Path("data/samples/frame_case.yaml"),
    sample_root: str | Path = Path("data/samples"),
    output_root: str | Path = Path("."),
) -> DemoResult:
    """Run the complete sample workflow from input validation to report."""
    paths = DemoPaths.build(frame_case=frame_case, sample_root=sample_root, output_root=output_root)
    completed_steps: list[str] = []

    config = validate_demo_input(paths)
    completed_steps.append("validate-input")

    load_cases, combinations = build_demo_loads(paths)
    completed_steps.append("build-loads")

    lira_rows = import_demo_lira(paths)
    completed_steps.append("import-lira")

    dataset_rows = build_demo_dataset(config, paths, load_cases, combinations, lira_rows)
    completed_steps.append("build-dataset")

    model = train_demo_model(config, paths, dataset_rows)
    completed_steps.append("train")

    prediction_rows = predict_demo_sections(paths, dataset_rows, model)
    completed_steps.append("predict")

    verified_rows = verify_demo_predictions(paths, dataset_rows, prediction_rows)
    completed_steps.append("verify")

    selected_section_id = write_demo_report(
        config=config,
        paths=paths,
        dataset_rows=dataset_rows,
        predictions=verified_rows,
        load_cases=load_cases,
        combinations=combinations,
    )
    completed_steps.append("report")

    return DemoResult(
        paths=paths,
        steps=tuple(completed_steps),
        selected_section_id=selected_section_id,
        output_files=(
            paths.ml_dataset,
            paths.predictions,
            paths.report,
            paths.model_artifact,
        ),
    )


def validate_demo_input(paths: DemoPaths) -> AppConfig:
    """Validate the demo YAML and sample input files."""
    missing = [
        path
        for path in [
            paths.frame_case,
            paths.section_catalog,
            paths.sp20_loads,
            paths.load_combinations,
            paths.lira_forces,
            paths.labels,
        ]
        if not path.exists()
    ]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing demo input files: {missing_text}")

    config = load_config(paths.frame_case)
    report = validate_config(config)
    if report.errors:
        message = "; ".join(f"{issue.path}: {issue.message}" for issue in report.errors)
        raise ValueError(f"Demo input validation failed: {message}")

    sections = load_section_catalog(paths.section_catalog)
    if not sections:
        raise ValueError("Demo section catalog is empty")
    return config


def build_demo_loads(paths: DemoPaths) -> tuple[list[SP20LoadCase], list[dict[str, str]]]:
    """Load and validate sample SP 20 load cases and combinations."""
    load_rows = _read_required_csv(paths.sp20_loads, LOAD_COLUMNS)
    combination_rows = _read_required_csv(paths.load_combinations, COMBINATION_COLUMNS)

    load_cases = [SP20LoadCase.model_validate(row) for row in load_rows]
    for row in load_rows:
        _require_number(row, "value", paths.sp20_loads)
        _require_number(row, "gamma_f", paths.sp20_loads)
    for row in combination_rows:
        _require_number(row, "factor", paths.load_combinations)

    return load_cases, combination_rows


def import_demo_lira(paths: DemoPaths) -> list[dict[str, str]]:
    """Validate and import sample LIRA element forces."""
    report = validate_lira_element_forces(paths.lira_forces)
    if not report.ok:
        message = "; ".join(issue.message for issue in report.issues)
        raise ValueError(f"Demo LIRA import validation failed: {message}")
    return import_lira_forces(paths.lira_forces)


def build_demo_dataset(
    config: AppConfig,
    paths: DemoPaths,
    load_cases: list[SP20LoadCase],
    combinations: list[dict[str, str]],
    lira_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build the single-row demo ML dataset."""
    labels = _read_required_csv(paths.labels, LABEL_COLUMNS)
    sections = load_section_catalog(paths.section_catalog)
    case_id = config.project.project_id
    label = _find_case_row(labels, case_id, paths.labels)
    section = _find_section(sections, label["target_section_id"])
    geometry = config.frame.geometry
    material = config.frame.material

    target_mass = _float_or_none(label["target_mass_kg_m"])
    if target_mass is None and section.mass_kg_m is not None:
        target_mass = section.mass_kg_m

    dataset_row = {
        "case_id": case_id,
        "span_m": _format_number(geometry.span_m),
        "eave_height_m": _format_number(geometry.eave_height_m),
        "ridge_height_m": _format_number(geometry.ridge_height_m),
        "roof_slope_deg": _format_number(geometry.computed_roof_slope_deg),
        "frame_spacing_m": _format_number(geometry.frame_spacing_m),
        "building_length_m": _format_optional_number(geometry.building_length_m),
        "frame_count": str(geometry.frame_count or ""),
        "support_left": config.frame.supports.left_base,
        "support_right": config.frame.supports.right_base,
        "steel_grade": material.steel_grade,
        "snow_value_kpa": _format_number(_max_load_value(load_cases, "snow")),
        "wind_value_kpa": _format_number(_max_load_value(load_cases, "wind")),
        "roof_dead_kpa": _format_number(_load_value(load_cases, "G_roof_dead")),
        "purlins_kpa": _format_number(_load_value(load_cases, "G_purlins_bracing")),
        "roof_live_kpa": _format_number(_load_value(load_cases, "Q_roof_maintenance")),
        "load_case_count": str(len(load_cases)),
        "load_combination_count": str(len({row["combo_id"] for row in combinations})),
        "section_catalog_count": str(len(sections)),
        "max_abs_n_kN": _format_number(_max_abs(lira_rows, "N_kN")),
        "max_abs_qy_kN": _format_number(_max_abs(lira_rows, "Qy_kN")),
        "max_abs_mz_kNm": _format_number(_max_abs(lira_rows, "Mz_kNm")),
        "max_abs_uy_mm": _format_number(_max_abs(lira_rows, "uy_mm")),
        "target_section_id": label["target_section_id"],
        "target_mass_kg_m": _format_optional_number(target_mass),
        "max_utilization_percent": _format_number(_max_abs(lira_rows, "utilization_percent")),
        "governing_combo": label["governing_combo"],
        "governing_element": label["governing_element"],
        "governing_check": label["governing_check"],
        "pass_status": label["pass_status"].strip().lower(),
    }
    dataset_rows = [dataset_row]
    _write_csv(paths.ml_dataset, DATASET_COLUMNS, dataset_rows)
    return dataset_rows


def train_demo_model(
    config: AppConfig,
    paths: DemoPaths,
    dataset_rows: list[dict[str, str]],
) -> FrequencySectionRecommender:
    """Train and save the baseline frequency recommender."""
    labels = [row["target_section_id"] for row in dataset_rows]
    model = FrequencySectionRecommender(top_k=config.ml.top_k).fit(labels)
    artifact = {
        "model_type": "frequency_section_recommender",
        "top_k": config.ml.top_k,
        "labels": model.predict_top_k(),
        "training_rows": len(dataset_rows),
        "warning": DEMO_WARNING_EN,
    }
    paths.model_artifact.parent.mkdir(parents=True, exist_ok=True)
    paths.model_artifact.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return model


def predict_demo_sections(
    paths: DemoPaths,
    dataset_rows: list[dict[str, str]],
    model: FrequencySectionRecommender,
) -> list[dict[str, str]]:
    """Write top-N section predictions for the demo case."""
    case_id = dataset_rows[0]["case_id"]
    sections = {section.section_id: section for section in load_section_catalog(paths.section_catalog)}
    prediction_rows = []
    for rank, section_id in enumerate(model.predict_top_k(), start=1):
        section = sections.get(section_id)
        prediction_rows.append(
            {
                "case_id": case_id,
                "rank": str(rank),
                "section_id": section_id,
                "mass_kg_m": _format_optional_number(section.mass_kg_m if section else None),
                "model_type": "frequency_section_recommender",
                "verification_status": "pending",
                "selected_for_report": "false",
                "verification_note": "",
            }
        )
    _write_csv(paths.predictions, PREDICTION_COLUMNS, prediction_rows)
    return prediction_rows


def verify_demo_predictions(
    paths: DemoPaths,
    dataset_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Verify predictions against the sample LIRA label, not against SP checks."""
    target_mass = _float(dataset_rows[0]["target_mass_kg_m"])
    target_passed = dataset_rows[0]["pass_status"] in {"true", "1", "yes", "y"}
    sections = {section.section_id: section for section in load_section_catalog(paths.section_catalog)}
    selected = False

    verified_rows: list[dict[str, str]] = []
    for row in prediction_rows:
        section = sections.get(row["section_id"])
        section_mass = section.mass_kg_m if section else None
        if section_mass is None:
            status = "failed_missing_section"
        elif target_passed and section_mass >= target_mass:
            status = "verified_by_demo_lira_label"
        else:
            status = "failed_demo_lira_label"

        row = dict(row)
        row["verification_status"] = status
        row["selected_for_report"] = "true" if status == "verified_by_demo_lira_label" and not selected else "false"
        row["verification_note"] = DEMO_WARNING_EN
        selected = selected or row["selected_for_report"] == "true"
        verified_rows.append(row)

    if not selected:
        raise ValueError("No demo prediction passed verification against the sample LIRA label")

    _write_csv(paths.predictions, PREDICTION_COLUMNS, verified_rows)
    return verified_rows


def write_demo_report(
    config: AppConfig,
    paths: DemoPaths,
    dataset_rows: list[dict[str, str]],
    predictions: list[dict[str, str]],
    load_cases: list[SP20LoadCase],
    combinations: list[dict[str, str]],
) -> str:
    """Generate the demo markdown report and return the selected section id."""
    selected = next(row for row in predictions if row["selected_for_report"] == "true")
    dataset = dataset_rows[0]
    lines = [
        "## Предупреждение",
        f"**Внимание:** {DEMO_WARNING_RU}",
        "",
        "## Demo Pipeline",
        "Выполнены шаги: " + " -> ".join(DEMO_STEPS) + ".",
        "",
        "## Исходные данные",
        f"- Проект: `{config.project.project_id}` / `{config.project.name}`",
        f"- Геометрия: пролёт {dataset['span_m']} м, карниз {dataset['eave_height_m']} м, "
        f"конёк {dataset['ridge_height_m']} м.",
        f"- Сортамент: `{paths.section_catalog}`",
        f"- Нагрузки: `{paths.sp20_loads}` ({len(load_cases)} load cases)",
        f"- Сочетания: `{paths.load_combinations}` ({len({row['combo_id'] for row in combinations})} combinations)",
        f"- Импорт ЛИРА: `{paths.lira_forces}`",
        "",
        "## Результат",
        f"- ML top-1: `{selected['section_id']}`",
        f"- Проверка демо-меткой ЛИРА: `{selected['verification_status']}`",
        f"- Эталонное сечение sample-набора: `{dataset['target_section_id']}`",
        f"- Максимальный процент использования sample-набора: {dataset['max_utilization_percent']}%",
        "",
        "## Созданные файлы",
        f"- `{paths.ml_dataset}`",
        f"- `{paths.predictions}`",
        f"- `{paths.model_artifact}`",
        f"- `{paths.report}`",
        "",
        "## Ограничения",
        "- Данные демонстрационные и не являются расчётной базой для реального объекта.",
        f"- {DEMO_WARNING_RU}",
    ]
    write_markdown_report(paths.report, "Steel Frame Designer Demo Report", lines)
    return selected["section_id"]


def _read_required_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    rows = read_csv_rows(path)
    if not rows:
        raise ValueError(f"CSV file is empty: {path}")
    missing = sorted(required_columns.difference(rows[0].keys()))
    if missing:
        raise ValueError(f"CSV file {path} misses columns: {', '.join(missing)}")
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _require_number(row: dict[str, str], column: str, path: Path) -> None:
    if _float_or_none(row.get(column, "")) is None:
        raise ValueError(f"Required numeric value is empty in {path}: {column}")


def _find_case_row(rows: list[dict[str, str]], case_id: str, path: Path) -> dict[str, str]:
    for row in rows:
        if row["case_id"] == case_id:
            return row
    raise ValueError(f"Case {case_id!r} not found in {path}")


def _find_section(sections: list[SectionProfile], section_id: str) -> SectionProfile:
    for section in sections:
        if section.section_id == section_id:
            return section
    raise ValueError(f"Section {section_id!r} not found in demo section catalog")


def _load_value(load_cases: list[SP20LoadCase], load_id: str) -> float:
    for load_case in load_cases:
        if load_case.load_id == load_id and load_case.value is not None:
            return load_case.value
    return 0.0


def _max_load_value(load_cases: list[SP20LoadCase], group: str) -> float:
    values = [load_case.value or 0.0 for load_case in load_cases if load_case.group.value == group]
    return max(values, default=0.0)


def _max_abs(rows: list[dict[str, str]], column: str) -> float:
    return max(abs(_float(row[column])) for row in rows)


def _float(value: str | float | int) -> float:
    parsed = _float_or_none(value)
    if parsed is None:
        raise ValueError(f"Expected numeric value, got {value!r}")
    return parsed


def _float_or_none(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return float(value)


def _format_number(value: float) -> str:
    return f"{value:.6g}"


def _format_optional_number(value: float | None) -> str:
    if value is None:
        return ""
    return _format_number(value)
