"""Geometry models for a 2D single-span gable frame."""

from __future__ import annotations

from math import atan, degrees, hypot
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


SupportType = Literal["fixed", "pinned", "hinged"]


class FrameNode(BaseModel):
    """A node in the basic N1-N5 frame scheme."""

    node_id: str
    x_m: float
    y_m: float


class FrameElement(BaseModel):
    """A line element in the basic E1-E4 frame scheme."""

    element_id: str
    role: str
    start_node_id: str
    end_node_id: str
    length_m: float = Field(gt=0)


class FrameGeometry(BaseModel):
    """Input geometry for a 2D one-span gable frame."""

    model_config = ConfigDict(populate_by_name=True)

    span_m: float = Field(gt=0)
    eave_height_m: float = Field(
        gt=0,
        validation_alias=AliasChoices("eave_height_m", "column_height_m"),
    )
    ridge_height_m: float = Field(gt=0)
    roof_slope_deg: float | None = Field(default=None, gt=0, lt=90)
    frame_spacing_m: float = Field(gt=0)
    building_length_m: float | None = Field(default=None, gt=0)
    frame_count: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_gable_geometry(self) -> "FrameGeometry":
        if self.ridge_height_m <= self.eave_height_m:
            raise ValueError("ridge_height_m must be greater than eave_height_m")
        return self

    @property
    def roof_rise_m(self) -> float:
        return self.ridge_height_m - self.eave_height_m

    @property
    def half_span_m(self) -> float:
        return self.span_m / 2.0

    @property
    def computed_roof_slope_deg(self) -> float:
        return degrees(atan(self.roof_rise_m / self.half_span_m))

    @property
    def roof_slope_percent(self) -> float:
        return self.roof_rise_m / self.half_span_m * 100.0

    @property
    def rafter_length_m(self) -> float:
        return hypot(self.half_span_m, self.roof_rise_m)

    @property
    def frame_axis_length_m(self) -> float:
        return 2.0 * self.eave_height_m + 2.0 * self.rafter_length_m

    def build_nodes(self) -> list[FrameNode]:
        return [
            FrameNode(node_id="N1", x_m=0.0, y_m=0.0),
            FrameNode(node_id="N2", x_m=0.0, y_m=self.eave_height_m),
            FrameNode(node_id="N3", x_m=self.half_span_m, y_m=self.ridge_height_m),
            FrameNode(node_id="N4", x_m=self.span_m, y_m=self.eave_height_m),
            FrameNode(node_id="N5", x_m=self.span_m, y_m=0.0),
        ]

    def build_elements(self) -> list[FrameElement]:
        return [
            FrameElement(
                element_id="E1",
                role="left_column",
                start_node_id="N1",
                end_node_id="N2",
                length_m=self.eave_height_m,
            ),
            FrameElement(
                element_id="E2",
                role="left_rafter",
                start_node_id="N2",
                end_node_id="N3",
                length_m=self.rafter_length_m,
            ),
            FrameElement(
                element_id="E3",
                role="right_rafter",
                start_node_id="N3",
                end_node_id="N4",
                length_m=self.rafter_length_m,
            ),
            FrameElement(
                element_id="E4",
                role="right_column",
                start_node_id="N4",
                end_node_id="N5",
                length_m=self.eave_height_m,
            ),
        ]
