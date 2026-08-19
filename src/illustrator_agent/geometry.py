"""Primitive editable path geometry."""

from __future__ import annotations

from collections.abc import Sequence

from py_ai_illustrator.model import ControlPoint, Path, Point, ProcessColor


def rectangle_path(
    item_id: str,
    *,
    x: float,
    top: float,
    width: float,
    height: float,
    fill: ProcessColor | None,
    stroke: ProcessColor | None = None,
    stroke_width: float = 1.0,
    name: str | None = None,
) -> Path:
    """Create an editable rectangle using top-left page coordinates."""

    if width <= 0 or height <= 0:
        raise ValueError("Rectangle dimensions must be positive")
    return Path(
        id=item_id,
        name=name,
        points=[
            Point(x, top - height),
            Point(x + width, top - height),
            Point(x + width, top),
            Point(x, top),
        ],
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
    )


def polyline_path(
    item_id: str,
    *,
    points: Sequence[tuple[float, float]],
    stroke: ProcessColor,
    stroke_width: float = 1.0,
    dash_pattern: Sequence[float] = (),
    dash_offset: float = 0.0,
    line_cap: str = "butt",
    line_join: str = "miter",
    name: str | None = None,
) -> Path:
    """Create an editable open polyline with native Illustrator stroke styling."""

    return Path(
        id=item_id,
        name=name,
        points=[Point(x, y) for x, y in points],
        closed=False,
        fill=None,
        stroke=stroke,
        stroke_width=stroke_width,
        dash_pattern=list(dash_pattern),
        dash_offset=dash_offset,
        line_cap=line_cap,
        line_join=line_join,
    )


def ellipse_path(
    item_id: str,
    *,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    fill: ProcessColor | None,
    stroke: ProcessColor | None = None,
    stroke_width: float = 1.0,
    name: str | None = None,
) -> Path:
    """Create an editable four-segment cubic Bézier ellipse."""

    if radius_x <= 0 or radius_y <= 0:
        raise ValueError("Ellipse radii must be positive")
    kappa = 0.5522847498307936
    x_handle = radius_x * kappa
    y_handle = radius_y * kappa
    return Path(
        id=item_id,
        name=name,
        points=[
            Point(
                center_x + radius_x,
                center_y,
                in_handle=ControlPoint(center_x + radius_x, center_y - y_handle),
                out_handle=ControlPoint(center_x + radius_x, center_y + y_handle),
                smooth=True,
            ),
            Point(
                center_x,
                center_y + radius_y,
                in_handle=ControlPoint(center_x + x_handle, center_y + radius_y),
                out_handle=ControlPoint(center_x - x_handle, center_y + radius_y),
                smooth=True,
            ),
            Point(
                center_x - radius_x,
                center_y,
                in_handle=ControlPoint(center_x - radius_x, center_y + y_handle),
                out_handle=ControlPoint(center_x - radius_x, center_y - y_handle),
                smooth=True,
            ),
            Point(
                center_x,
                center_y - radius_y,
                in_handle=ControlPoint(center_x - x_handle, center_y - radius_y),
                out_handle=ControlPoint(center_x + x_handle, center_y - radius_y),
                smooth=True,
            ),
        ],
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
    )
