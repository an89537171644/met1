import pytest
from pydantic import ValidationError

from steel_frame_designer.geometry import FrameGeometry
from steel_frame_designer.lira_import import LiraImportRecord
from steel_frame_designer.load_combinations import LoadCombination, LoadCombinationTerm
from steel_frame_designer.materials import SteelMaterial
from steel_frame_designer.ml_data import MLCase
from steel_frame_designer.sections import SectionProfile
from steel_frame_designer.sp20_loads import LoadGroup, SP20LoadCase


def test_issue_1_required_models_can_be_created() -> None:
    geometry = FrameGeometry(
        span_m=18.0,
        eave_height_m=6.0,
        ridge_height_m=8.0,
        frame_spacing_m=6.0,
    )
    material = SteelMaterial(steel_grade="C345")
    section = SectionProfile(section_id="I30_demo", type="i_beam", mass_kg_m=36.5)
    load_case = SP20LoadCase(
        case_id="case_0001",
        load_id="S_symmetric",
        group=LoadGroup.SNOW,
        value=1.8,
        unit="kPa",
        tributary_width_m=6.0,
    )
    combination = LoadCombination(
        combo_id="ULS_001",
        case_id="case_0001",
        limit_state="ULS",
        terms=[LoadCombinationTerm(load_id="S_symmetric", factor=1.4)],
    )
    lira_record = LiraImportRecord(
        case_id="case_0001",
        lira_model_file="models/case_0001.lir",
        success=True,
    )
    ml_case = MLCase(
        case_id="case_0001",
        span_m=18.0,
        eave_height_m=6.0,
        ridge_height_m=8.0,
        frame_spacing_m=6.0,
        target_section_id="I30_demo",
    )

    assert geometry.computed_roof_slope_deg > 0
    assert material.steel_grade == "C345"
    assert section.mass_kg_m == 36.5
    assert load_case.group is LoadGroup.SNOW
    assert combination.terms[0].factor == 1.4
    assert lira_record.success is True
    assert ml_case.target_section_id == "I30_demo"


def test_geometry_validation_error_is_clear() -> None:
    with pytest.raises(ValidationError) as exc_info:
        FrameGeometry(
            span_m=18.0,
            eave_height_m=8.0,
            ridge_height_m=8.0,
            frame_spacing_m=6.0,
        )

    assert "ridge_height_m must be greater than eave_height_m" in str(exc_info.value)
