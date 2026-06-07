from pathlib import Path

from steel_frame_designer.config import load_config, validate_config, validation_warnings


def test_load_current_example_config() -> None:
    config = load_config("config.example.yaml")

    assert config.project.project_id == "example_001"
    assert config.frame.geometry.span_m == 18.0
    assert round(config.frame.geometry.computed_roof_slope_deg, 2) == 12.53
    assert config.ml.top_k == 5


def test_load_flat_scaffold_config_shape(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
project:
  name: test-project
  version: "0.1.0"
norms:
  sp16:
    code: "SP 16.13330"
    edition: "2017"
  sp20:
    code: "SP 20.13330"
    edition: "2016"
frame:
  span_m: 24.0
  column_height_m: 6.0
  ridge_height_m: 9.0
  frame_spacing_m: 6.0
  support_type: pinned
ml:
  top_k: 3
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.project.name == "test-project"
    assert config.frame.geometry.eave_height_m == 6.0
    assert config.frame.supports.left_base == "pinned"
    assert config.ml.top_k == 3


def test_validation_warnings_for_template_config() -> None:
    config = load_config("config.example.yaml")

    warnings = validation_warnings(config)

    assert any("City or region is not set" in warning for warning in warnings)


def test_validate_config_reports_required_empty_fields() -> None:
    config = load_config("config.example.yaml")

    report = validate_config(config)

    assert not report.ok
    error_paths = {issue.path for issue in report.errors}
    assert "sp20_loads.permanent.roof_dead_kpa" in error_paths
    assert "sp20_loads.snow.normative_snow_value_kpa" in error_paths
    assert "sp20_loads.wind.normative_wind_value_kpa" in error_paths


def test_validate_config_accepts_complete_required_fields(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
project:
  project_id: case_ok
  name: complete-config
  norms:
    steel_design: "SP 16.13330.2017"
    steel_design_edition: "2017 change-set"
    loads: "SP 20.13330.2016"
    loads_edition: "2016 change-set"
frame:
  geometry:
    span_m: 18.0
    eave_height_m: 6.0
    ridge_height_m: 8.0
    frame_spacing_m: 6.0
  material:
    steel_grade: C345
sp20_loads:
  location:
    city: Moscow
    terrain_type: B
  permanent:
    roof_dead_kpa: 0.35
    purlins_kpa: 0.08
  snow:
    enabled: true
    normative_snow_value_kpa: 1.8
  wind:
    enabled: true
    normative_wind_value_kpa: 0.38
  roof_live:
    enabled: true
    value_kpa: 0.7
""",
        encoding="utf-8",
    )

    report = validate_config(load_config(config_file))

    assert report.ok
    assert report.errors == []
