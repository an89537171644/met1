from pathlib import Path

from typer.testing import CliRunner

from steel_frame_designer.cli import app
from steel_frame_designer.config import load_config
from steel_frame_designer.demo import (
    DEMO_STEPS,
    DemoPaths,
    build_demo_dataset,
    build_demo_loads,
    import_demo_lira,
    validate_demo_input,
)
from steel_frame_designer.lira_import import validate_lira_element_forces
from steel_frame_designer.sections import load_section_catalog


SAMPLE_ROOT = Path("data/samples")
FRAME_CASE = SAMPLE_ROOT / "frame_case.yaml"


def test_sample_geometry_builds_expected_frame() -> None:
    config = load_config(FRAME_CASE)
    frame = config.frame.geometry.build_frame()

    assert config.project.project_id == "demo_001"
    assert config.frame.geometry.span_m == 18.0
    assert round(config.frame.geometry.computed_roof_slope_deg, 2) == 12.53
    assert frame.node_ids == ["N1", "N2", "N3", "N4", "N5"]
    assert frame.element_roles == ["left_column", "left_rafter", "right_rafter", "right_column"]


def test_sample_section_catalog_contains_ordered_demo_sections() -> None:
    sections = load_section_catalog(SAMPLE_ROOT / "section_catalog.csv")

    assert [section.section_id for section in sections] == [
        "I20_demo",
        "I24_demo",
        "I30_demo",
        "I36_demo",
    ]
    assert [section.mass_kg_m for section in sections] == sorted(
        section.mass_kg_m for section in sections if section.mass_kg_m is not None
    )
    assert sections[2].Wx_cm3 == 480


def test_sample_lira_import_is_valid() -> None:
    report = validate_lira_element_forces(SAMPLE_ROOT / "lira_element_forces.csv")
    rows = import_demo_lira(DemoPaths.build())

    assert report.ok
    assert report.row_count == 5
    assert any(row["element_id"] == "E2" for row in rows)


def test_demo_ml_dataset_formation(tmp_path) -> None:
    paths = DemoPaths.build(output_root=tmp_path)
    config = validate_demo_input(paths)
    load_cases, combinations = build_demo_loads(paths)
    lira_rows = import_demo_lira(paths)

    dataset_rows = build_demo_dataset(config, paths, load_cases, combinations, lira_rows)

    assert paths.ml_dataset.exists()
    assert dataset_rows[0]["case_id"] == "demo_001"
    assert dataset_rows[0]["target_section_id"] == "I30_demo"
    assert dataset_rows[0]["max_abs_mz_kNm"] == "118"
    assert dataset_rows[0]["load_case_count"] == "8"


def test_run_demo_command_creates_expected_outputs(tmp_path) -> None:
    result = CliRunner().invoke(app, ["run-demo", "--output-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    for step in DEMO_STEPS:
        assert f"{step}: ok" in result.output
    assert "Selected section: I30_demo" in result.output

    assert (tmp_path / "data/processed/ml_dataset.csv").exists()
    assert (tmp_path / "data/output/predictions.csv").exists()
    assert (tmp_path / "reports/demo_report.md").exists()
    assert (tmp_path / "artifacts/baseline_model.json").exists()
    report = (tmp_path / "reports/demo_report.md").read_text(encoding="utf-8")
    assert "ML-рекомендация не является нормативным расчётом по СП 16/СП 20" in report
