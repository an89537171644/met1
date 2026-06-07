import pytest
from pydantic import ValidationError

from steel_frame_designer.geometry import FrameElement, FrameGeometry, FrameNode, GableFrame


def test_valid_gable_geometry_computes_derived_values() -> None:
    frame = FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    assert frame.roof_rise_m == 3
    assert frame.half_span_m == 12
    assert frame.roof_slope_percent == 25
    assert round(frame.computed_roof_slope_deg, 2) == 14.04
    assert [node.node_id for node in frame.build_nodes()] == ["N1", "N2", "N3", "N4", "N5"]
    assert [element.element_id for element in frame.build_elements()] == ["E1", "E2", "E3", "E4"]


def test_gable_frame_object_contains_connected_nodes_and_elements() -> None:
    geometry = FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    frame = geometry.build_frame()

    assert frame.node_ids == ["N1", "N2", "N3", "N4", "N5"]
    assert frame.element_ids == ["E1", "E2", "E3", "E4"]
    assert frame.element_roles == ["left_column", "left_rafter", "right_rafter", "right_column"]
    assert round(frame.total_axis_length_m, 3) == round(geometry.frame_axis_length_m, 3)


def test_column_height_alias_is_accepted() -> None:
    frame = FrameGeometry(span_m=24, column_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    assert frame.eave_height_m == 6


def test_ridge_must_be_above_eave() -> None:
    with pytest.raises(ValueError):
        FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=6, frame_spacing_m=6)


def test_gable_frame_rejects_unknown_element_node() -> None:
    geometry = FrameGeometry(span_m=24, eave_height_m=6, ridge_height_m=9, frame_spacing_m=6)

    with pytest.raises(ValidationError) as exc_info:
        GableFrame(
            geometry=geometry,
            nodes=[FrameNode(node_id="N1", x_m=0, y_m=0)],
            elements=[
                FrameElement(
                    element_id="E1",
                    role="left_column",
                    start_node_id="N1",
                    end_node_id="N2",
                    length_m=6,
                )
            ],
        )

    assert "references unknown frame node" in str(exc_info.value)
