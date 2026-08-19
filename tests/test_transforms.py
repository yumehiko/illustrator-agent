import pytest
from py_ai_illustrator.model import Color, LayerItemRef

from illustrator_agent import (
    AffineTransform,
    RenderedComponent,
    TextBlock,
    TextStyle,
    ellipse_path,
    rectangle_path,
)


def test_rigid_component_transform_rotates_paths_text_and_dimensions() -> None:
    text = TextBlock(
        id="label", text="ROTATE", width=100, wrap=False, style=TextStyle(rotation=5)
    ).render(x=10, top=30)
    panel = rectangle_path("panel", x=0, top=50, width=100, height=50, fill=Color(1, 1, 1))
    component = RenderedComponent(
        width=100,
        height=50,
        paths=[panel],
        text_frames=text.text_frames,
        item_order=[LayerItemRef("path", "panel"), *text.item_order],
    )

    rotated = component.transformed(AffineTransform.rotation(90))

    assert rotated.width == pytest.approx(50)
    assert rotated.height == pytest.approx(100)
    assert (rotated.paths[0].points[0].x, rotated.paths[0].points[0].y) == pytest.approx((0, 0))
    assert (rotated.text_frames[0].x, rotated.text_frames[0].y) == pytest.approx((-20.4, 10))
    assert rotated.text_frames[0].rotation == pytest.approx(95)
    assert rotated.item_order == component.item_order


def test_affine_transform_rotates_bezier_handles_with_anchor() -> None:
    ellipse = ellipse_path(
        "mark", center_x=20, center_y=30, radius_x=10, radius_y=5, fill=Color(1, 1, 1)
    )

    transformed = RenderedComponent(width=20, height=10, paths=[ellipse]).transformed(
        AffineTransform.rotation(90)
    )
    point = transformed.paths[0].points[0]

    assert (point.x, point.y) == pytest.approx((-30, 30))
    assert point.in_handle is not None
    assert (point.in_handle.x, point.in_handle.y) == pytest.approx((-27.238576, 30))


def test_component_with_text_rejects_non_rigid_scale_as_current_capability_limit() -> None:
    component = TextBlock(id="label", text="No stretch", width=100).render(x=0, top=20)

    with pytest.raises(ValueError, match="currently require a rigid transform"):
        component.transformed(AffineTransform(a=2, d=1))
