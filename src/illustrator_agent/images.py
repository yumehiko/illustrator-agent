"""Deterministic placement of editable linked images."""

from __future__ import annotations

import math
from typing import Literal

from py_ai_illustrator.model import LinkedImage

FitPolicy = Literal["contain"]
HorizontalAlignment = Literal["left", "center", "right"]
VerticalAlignment = Literal["top", "center", "bottom"]


def _positive_finite(value: float, *, name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def _finite(value: float, *, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def fit_linked_image(
    *,
    id: str,
    source: str,
    intrinsic_width: float,
    intrinsic_height: float,
    target_x: float,
    target_top: float,
    target_width: float,
    target_height: float,
    fit_policy: FitPolicy,
    horizontal_alignment: HorizontalAlignment,
    vertical_alignment: VerticalAlignment,
    name: str | None = None,
) -> LinkedImage:
    """Fit a linked image inside a target box without stretching or cropping."""

    if not id:
        raise ValueError("A linked image id must not be empty")
    if not source.strip() or "\x00" in source:
        raise ValueError("A linked image source must be a non-empty path")
    intrinsic_width = _positive_finite(intrinsic_width, name="intrinsic_width")
    intrinsic_height = _positive_finite(intrinsic_height, name="intrinsic_height")
    target_x = _finite(target_x, name="target_x")
    target_top = _finite(target_top, name="target_top")
    target_width = _positive_finite(target_width, name="target_width")
    target_height = _positive_finite(target_height, name="target_height")
    if fit_policy != "contain":
        raise ValueError("fit_policy must be 'contain'")
    if horizontal_alignment not in {"left", "center", "right"}:
        raise ValueError("horizontal_alignment must be 'left', 'center', or 'right'")
    if vertical_alignment not in {"top", "center", "bottom"}:
        raise ValueError("vertical_alignment must be 'top', 'center', or 'bottom'")

    scale = min(target_width / intrinsic_width, target_height / intrinsic_height)
    width = intrinsic_width * scale
    height = intrinsic_height * scale
    horizontal_factor = {"left": 0.0, "center": 0.5, "right": 1.0}[horizontal_alignment]
    vertical_factor = {"top": 0.0, "center": 0.5, "bottom": 1.0}[vertical_alignment]
    x = target_x + (target_width - width) * horizontal_factor
    y = target_top - (target_height - height) * vertical_factor
    return LinkedImage(
        id=id,
        name=name,
        source=source,
        x=x,
        y=y,
        width=width,
        height=height,
    )
