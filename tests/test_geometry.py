from py_ai_illustrator.model import Color

from illustrator_agent import ellipse_path, polyline_path, rectangle_path


def test_rectangle_uses_top_left_coordinates() -> None:
    rectangle = rectangle_path(
        "panel", x=10, top=80, width=40, height=20, fill=Color(1, 1, 1)
    )

    assert [(point.x, point.y) for point in rectangle.points] == [
        (10, 60),
        (50, 60),
        (50, 80),
        (10, 80),
    ]


def test_polyline_keeps_native_stroke_style() -> None:
    route = polyline_path(
        "route",
        points=[(10, 20), (30, 50), (80, 40)],
        stroke=Color(0.1, 0.4, 0.8),
        stroke_width=4,
        dash_pattern=(12, 6),
        dash_offset=2,
        line_cap="round",
        line_join="bevel",
    )

    assert not route.closed
    assert route.dash_pattern == [12, 6]
    assert route.dash_offset == 2
    assert route.line_cap == "round"
    assert route.line_join == "bevel"


def test_ellipse_has_editable_bezier_handles() -> None:
    ellipse = ellipse_path(
        "mark", center_x=20, center_y=30, radius_x=10, radius_y=5, fill=Color(1, 1, 1)
    )

    assert len(ellipse.points) == 4
    assert all(point.smooth for point in ellipse.points)
    assert all(point.in_handle and point.out_handle for point in ellipse.points)
