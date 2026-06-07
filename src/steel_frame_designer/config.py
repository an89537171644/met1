"""Application configuration models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .geometry import FrameGeometry, SupportType
from .materials import SteelMaterial


class ProjectNorms(BaseModel):
    model_config = ConfigDict(extra="ignore")

    steel_design: str = "SP 16.13330.2017"
    steel_design_edition: str = ""
    loads: str = "SP 20.13330.2016"
    loads_edition: str = ""


class ProjectInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = "example_001"
    name: str = Field(default="steel_frame_single_section", min_length=1)
    version: str = "0.1.0"
    norms: ProjectNorms = Field(default_factory=ProjectNorms)


class PathConfig(BaseModel):
    input_dir: Path = Path("data/input")
    output_dir: Path = Path("data/output")
    templates_dir: Path = Path("data/templates")
    reports_dir: Path = Path("reports")
    logs_dir: Path = Path("logs")


class FrameSupports(BaseModel):
    left_base: SupportType = "fixed"
    right_base: SupportType = "fixed"


class FrameConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["gable_single_span_2d"] = "gable_single_span_2d"
    single_section_for: list[str] = Field(
        default_factory=lambda: ["left_column", "left_rafter", "right_rafter", "right_column"]
    )
    geometry: FrameGeometry
    supports: FrameSupports = Field(default_factory=FrameSupports)
    material: SteelMaterial = Field(default_factory=lambda: SteelMaterial(steel_grade="C345"))


class SectionCatalogConfig(BaseModel):
    file: Path = Path("data/sections/section_catalog.csv")
    section_type: str = "i_beam_or_welded_i"
    sort_by: str = "mass_kg_m"


class SP20LocationConfig(BaseModel):
    city: str | None = None
    region: str | None = None
    snow_region: str | int | None = None
    wind_region: str | int | None = None
    terrain_type: str | None = None
    ice_region: str | int | None = None
    temperature_region: str | int | None = None


class PermanentLoadsConfig(BaseModel):
    steel_self_weight: str = "auto_from_section"
    roof_dead_kpa: float | None = None
    purlins_kpa: float | None = None
    bracing_kpa: float | None = None
    wall_cladding_kpa: float | None = None
    equipment_kpa: float = 0.0


class SnowLoadsConfig(BaseModel):
    enabled: bool = True
    normative_snow_value_kpa: float | None = None
    cases: list[str] = Field(
        default_factory=lambda: ["S_symmetric", "S_left_unbalanced", "S_right_unbalanced"]
    )


class WindLoadsConfig(BaseModel):
    enabled: bool = True
    normative_wind_value_kpa: float | None = None
    internal_pressure: str = "consider_if_openings"
    cases: list[str] = Field(default_factory=lambda: ["W_plus_x", "W_minus_x"])


class RoofLiveLoadConfig(BaseModel):
    enabled: bool = True
    value_kpa: float | None = None


class TemperatureConfig(BaseModel):
    enabled: bool = False
    t_min_c: float | None = None
    t_max_c: float | None = None
    t_install_c: float | None = None


class EnabledConfig(BaseModel):
    enabled: bool = False


class SP20LoadsConfig(BaseModel):
    location: SP20LocationConfig = Field(default_factory=SP20LocationConfig)
    permanent: PermanentLoadsConfig = Field(default_factory=PermanentLoadsConfig)
    snow: SnowLoadsConfig = Field(default_factory=SnowLoadsConfig)
    wind: WindLoadsConfig = Field(default_factory=WindLoadsConfig)
    roof_live: RoofLiveLoadConfig = Field(default_factory=RoofLiveLoadConfig)
    temperature: TemperatureConfig = Field(default_factory=TemperatureConfig)
    cranes: EnabledConfig = Field(default_factory=EnabledConfig)
    ice: EnabledConfig = Field(default_factory=EnabledConfig)
    special: EnabledConfig = Field(default_factory=EnabledConfig)


class LoadCombinationConfig(BaseModel):
    source: str = "sp20"
    file: Path = Path("data/input/load_combinations.csv")
    generate_automatically: bool = True


class LiraImportConfig(BaseModel):
    raw_dir: Path = Path("data/raw/lira_exports")
    processed_dir: Path = Path("data/processed")
    required_exports: list[str] = Field(
        default_factory=lambda: [
            "model_index",
            "element_forces",
            "nodal_displacements",
            "support_reactions",
            "section_checks",
            "selected_sections",
        ]
    )


class MLConfig(BaseModel):
    dataset_dir: Path = Path("data/datasets")
    target: str = "selected_single_section"
    prediction_mode: str = "top_k_classification_with_verification"
    top_k: int = Field(default=5, ge=1, le=20)
    safety_rule: str = "predicted_section_must_be_verified"


class ReportsConfig(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["markdown", "csv"])


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project: ProjectInfo = Field(default_factory=ProjectInfo)
    paths: PathConfig = Field(default_factory=PathConfig)
    frame: FrameConfig
    section_catalog: SectionCatalogConfig = Field(default_factory=SectionCatalogConfig)
    sp20_loads: SP20LoadsConfig = Field(default_factory=SP20LoadsConfig)
    load_combinations: LoadCombinationConfig = Field(default_factory=LoadCombinationConfig)
    lira_import: LiraImportConfig = Field(default_factory=LiraImportConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)

    @model_validator(mode="before")
    @classmethod
    def normalize_scaffold_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # The overlay scaffold used a flatter frame shape. Accept it to keep examples portable.
        frame = data.get("frame")
        if isinstance(frame, dict) and "geometry" not in frame and "span_m" in frame:
            data = dict(data)
            support_type = frame.get("support_type", "fixed")
            data["frame"] = {
                "type": "gable_single_span_2d",
                "geometry": {
                    "span_m": frame.get("span_m"),
                    "eave_height_m": frame.get("column_height_m", frame.get("eave_height_m")),
                    "ridge_height_m": frame.get("ridge_height_m"),
                    "frame_spacing_m": frame.get("frame_spacing_m"),
                },
                "supports": {"left_base": support_type, "right_base": support_type},
                "material": {"steel_grade": "C345"},
            }

        # Accept a top-level norms block from early scaffolds.
        if isinstance(data.get("norms"), dict):
            data = dict(data)
            project = dict(data.get("project") or {})
            norms = data["norms"]
            sp16 = norms.get("sp16", {})
            sp20 = norms.get("sp20", {})
            project["norms"] = {
                "steel_design": f"{sp16.get('code', 'SP 16.13330')} {sp16.get('edition', '2017')}",
                "steel_design_edition": sp16.get("change", ""),
                "loads": f"{sp20.get('code', 'SP 20.13330')} {sp20.get('edition', '2016')}",
                "loads_edition": sp20.get("change", ""),
            }
            data["project"] = project

        return data


def load_config(path: str | Path = "config.example.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(data)


def ensure_project_dirs(config: AppConfig) -> None:
    for directory in [
        config.paths.input_dir,
        config.paths.output_dir,
        config.paths.templates_dir,
        config.paths.reports_dir,
        config.paths.logs_dir,
        config.lira_import.raw_dir,
        config.lira_import.processed_dir,
        config.ml.dataset_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def validation_warnings(config: AppConfig) -> list[str]:
    warnings: list[str] = []
    if not config.project.norms.steel_design_edition:
        warnings.append("project.norms.steel_design_edition is not set")
    if not config.project.norms.loads_edition:
        warnings.append("project.norms.loads_edition is not set")
    if config.sp20_loads.snow.enabled and config.sp20_loads.snow.normative_snow_value_kpa is None:
        warnings.append("sp20_loads.snow.normative_snow_value_kpa is not set")
    if config.sp20_loads.wind.enabled and config.sp20_loads.wind.normative_wind_value_kpa is None:
        warnings.append("sp20_loads.wind.normative_wind_value_kpa is not set")
    if config.sp20_loads.permanent.roof_dead_kpa is None:
        warnings.append("sp20_loads.permanent.roof_dead_kpa is not set")
    return warnings
