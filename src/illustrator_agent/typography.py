"""Typography values and semantic text components."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from py_ai_illustrator.model import Color, ProcessColor, TextFrame

from .composition import RenderedComponent
from .text_layout import OverflowPolicy, TextLayoutResult, TextMeasurer, evaluate_text_layout


@dataclass(frozen=True, slots=True)
class FontSpec:
    """An installed Illustrator font identified by its PostScript name."""

    postscript_name: str
    family: str | None = None
    style: str | None = None

    def __post_init__(self) -> None:
        if not self.postscript_name or any(char.isspace() for char in self.postscript_name):
            raise ValueError("postscript_name must be a non-empty PostScript name")


@dataclass(frozen=True, slots=True)
class TextStyle:
    """Reusable typography for semantic text blocks."""

    font_size: float = 12.0
    font: FontSpec = field(default_factory=lambda: FontSpec("Helvetica"))
    tracking: float = 0.0
    rotation: float = 0.0
    fill: ProcessColor = field(default_factory=lambda: Color(0.0, 0.0, 0.0))
    line_height_ratio: float = 1.25

    def __post_init__(self) -> None:
        if self.font_size <= 0 or self.line_height_ratio <= 0:
            raise ValueError("Text size and line height must be positive")
        if not isinstance(self.font, FontSpec):
            raise TypeError("font must be a FontSpec")
        if not math.isfinite(self.tracking):
            raise ValueError("tracking must be finite")
        if not math.isfinite(self.rotation):
            raise ValueError("rotation must be finite")


@dataclass(frozen=True, slots=True)
class TextBlock:
    """Meaningful text rendered as editable, natively aligned point text."""

    id: str
    text: str
    width: float
    style: TextStyle = field(default_factory=TextStyle)
    alignment: str = "left"
    wrap: bool = True
    name: str | None = None
    text_measurer: TextMeasurer | None = None
    overflow_policy: OverflowPolicy = OverflowPolicy.PROVISIONAL

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("A text block id must not be empty")
        if self.width <= 0:
            raise ValueError("A text block width must be positive")
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("alignment must be 'left', 'center', or 'right'")
        if not isinstance(self.overflow_policy, OverflowPolicy):
            raise TypeError("overflow_policy must be an OverflowPolicy")

    @property
    def layout_result(self) -> TextLayoutResult:
        return evaluate_text_layout(
            self.text,
            max_width=self.width,
            font_postscript_name=self.style.font.postscript_name,
            font_size=self.style.font_size,
            tracking=self.style.tracking,
            wrap=self.wrap,
            measurer=self.text_measurer,
            policy=self.overflow_policy,
        )

    @property
    def lines(self) -> tuple[str, ...]:
        result = self.layout_result
        result.require_renderable()
        return result.lines

    def layout_report(self) -> dict[str, object]:
        """Return the explicit measurement and overflow decision evidence."""

        return self.layout_result.to_dict()

    @property
    def height(self) -> float:
        return self.style.font_size + (len(self.lines) - 1) * (
            self.style.font_size * self.style.line_height_ratio
        )

    def render(self, *, x: float, top: float) -> RenderedComponent:
        if self.alignment == "right":
            anchor_x = x + self.width
        elif self.alignment == "center":
            anchor_x = x + self.width / 2
        else:
            anchor_x = x
        line_height = self.style.font_size * self.style.line_height_ratio
        frames = [
            TextFrame(
                id=f"{self.id}.line-{index}",
                name=self.name or self.id,
                text=value,
                x=anchor_x,
                y=top - self.style.font_size * 0.8 - index * line_height,
                font_size=self.style.font_size,
                font_name=self.style.font.postscript_name,
                tracking=self.style.tracking,
                rotation=self.style.rotation,
                fill=self.style.fill,
                alignment=self.alignment,
            )
            for index, value in enumerate(self.lines)
        ]
        return RenderedComponent(width=self.width, height=self.height, text_frames=frames)


@dataclass(frozen=True, slots=True)
class AreaTextBlock:
    """A paragraph that becomes one reflowable native Illustrator area text."""

    id: str
    text: str
    width: float
    height: float
    style: TextStyle = field(default_factory=TextStyle)
    alignment: str = "left"
    name: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("An area text block id must not be empty")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Area text block dimensions must be positive")
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("alignment must be 'left', 'center', or 'right'")

    def render(self, *, x: float, top: float) -> RenderedComponent:
        frame = TextFrame(
            id=self.id,
            name=self.name or self.id,
            text=self.text.replace("\r\n", "\n").replace("\r", "\n"),
            x=x,
            y=top,
            font_size=self.style.font_size,
            font_name=self.style.font.postscript_name,
            tracking=self.style.tracking,
            rotation=self.style.rotation,
            area_width=self.width,
            area_height=self.height,
            leading=self.style.font_size * self.style.line_height_ratio,
            fill=self.style.fill,
            alignment=self.alignment,
        )
        return RenderedComponent(width=self.width, height=self.height, text_frames=[frame])
