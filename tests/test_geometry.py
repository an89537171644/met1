import pytest

from steel_frame_designer.geometry import FrameGeometry


def test_valid_gable_geometry_computes_derived_values() -> None:
    frame = FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    assert frame.roof_rise_m == 3
    assert frame.half_span_m == 12
    assert frame.roof_slope_percent == 25
    assert round(frame.computed_roof_slope_deg, 2) == 14.04
    assert [node.node_id for node in frame.build_nodes()] == ["N1", "N2", "N3", "N4", "N5"]
    assert [element.element_id for element in frame.build_elements()] == ["E1", "E2", "E3", "E4"]


def test_column_height_alias_is_accepted() -> None:
    frame = FrameGeometry(span_m=24, column_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    assert frame.eave_height_m == 6


def test_ridge_must_be_above_eave() -> None:
    with pytest.raises(ValueError):
        FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=6, frame_spacing_m=6)
