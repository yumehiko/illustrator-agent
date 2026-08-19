"""Affine transforms for editable graphic IR items."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from py_ai_illustrator.model import ControlPoint, Group, LinkedImage, Path, Point, TextFrame


@dataclass(frozen=True, slots=True)
class AffineTransform:
    """A 2D affine matrix used to place reusable rendered components."""

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    tx: float = 0.0
    ty: float = 0.0

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value) for value in (self.a, self.b, self.c, self.d, self.tx, self.ty)
        ):
            raise ValueError("Affine transform values must be finite")

    @classmethod
    def rotation(
        cls,
        degrees: float,
        *,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> AffineTransform:
        radians = math.radians(degrees)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        return cls(
            a=cosine,
            b=sine,
            c=-sine,
            d=cosine,
            tx=origin_x - cosine * origin_x + sine * origin_y,
            ty=origin_y - sine * origin_x - cosine * origin_y,
        )

    @classmethod
    def translation(cls, x: float, y: float) -> AffineTransform:
        return cls(tx=x, ty=y)

    @property
    def rotation_degrees(self) -> float:
        if not self.is_rigid:
            raise ValueError("Text rotation requires a rigid transform")
        return math.degrees(math.atan2(self.b, self.a))

    @property
    def is_rigid(self) -> bool:
        tolerance = 1e-9
        return (
            math.isclose(self.a * self.a + self.b * self.b, 1.0, abs_tol=tolerance)
            and math.isclose(self.c * self.c + self.d * self.d, 1.0, abs_tol=tolerance)
            and math.isclose(self.a * self.c + self.b * self.d, 0.0, abs_tol=tolerance)
            and math.isclose(self.a * self.d - self.b * self.c, 1.0, abs_tol=tolerance)
        )

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.a * x + self.c * y + self.tx,
            self.b * x + self.d * y + self.ty,
        )


def _transform_control(
    point: ControlPoint | None, transform: AffineTransform
) -> ControlPoint | None:
    if point is None:
        return None
    x, y = transform.apply(point.x, point.y)
    return ControlPoint(x, y)


def transform_path(path: Path, transform: AffineTransform) -> Path:
    """Return an editable path with anchors and Bézier handles transformed."""

    return replace(
        path,
        points=[
            Point(
                *transform.apply(point.x, point.y),
                in_handle=_transform_control(point.in_handle, transform),
                out_handle=_transform_control(point.out_handle, transform),
                smooth=point.smooth,
            )
            for point in path.points
        ],
    )


def transform_text(text: TextFrame, transform: AffineTransform) -> TextFrame:
    """Return editable point text placed by a rigid affine transform.

    The rigid-only rule reflects the current text IR/backend capability. It is
    not a product-level prohibition on scaled or skewed text.
    """

    if not transform.is_rigid:
        raise ValueError("TextFrame currently supports rigid transforms only")
    x, y = transform.apply(text.x, text.y)
    return replace(text, x=x, y=y, rotation=text.rotation + transform.rotation_degrees)


def transform_image(image: LinkedImage, transform: AffineTransform) -> LinkedImage:
    """Return a linked image placed by a rigid affine transform.

    The rigid-only rule reflects the current image IR/backend capability.
    """

    if not transform.is_rigid:
        raise ValueError("LinkedImage currently supports rigid transforms only")
    x, y = transform.apply(image.x, image.y)
    return replace(image, x=x, y=y, rotation=image.rotation + transform.rotation_degrees)


def transform_group(group: Group, transform: AffineTransform) -> Group:
    """Transform every editable descendant while preserving group semantics."""

    return replace(
        group,
        paths=[transform_path(path, transform) for path in group.paths],
        text_frames=[transform_text(text, transform) for text in group.text_frames],
        linked_images=[transform_image(image, transform) for image in group.linked_images],
        compound_paths=[
            replace(compound, paths=[transform_path(path, transform) for path in compound.paths])
            for compound in group.compound_paths
        ],
        clipping_groups=[
            replace(
                clipping,
                clipping_path=transform_path(clipping.clipping_path, transform),
                paths=[transform_path(path, transform) for path in clipping.paths],
            )
            for clipping in group.clipping_groups
        ],
        groups=[transform_group(child, transform) for child in group.groups],
    )
