"""Deterministic editable table component."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from py_ai_illustrator.model import Color, Layer, LayerItemRef, Path, Point, ProcessColor, TextFrame

from .composition import RenderedComponent
from .text_layout import wrap_text_approximately
from .typography import FontSpec

CellFormatter = Callable[[Any], str]
CellAccessor = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class _TableLayout:
    header_lines: tuple[tuple[str, ...], ...]
    header_height: float
    row_lines: tuple[tuple[tuple[str, ...], ...], ...]
    row_heights: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class TableColumn:
    """A semantic table column, including value lookup and presentation."""

    key: str
    title: str
    width: float
    alignment: str = "left"
    wrap: bool = False
    formatter: CellFormatter | None = None
    accessor: CellAccessor | None = None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("A table column key must not be empty")
        if self.width <= 0:
            raise ValueError("A table column width must be positive")
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("alignment must be 'left', 'center', or 'right'")

    def text_for(self, row: Mapping[str, Any]) -> str:
        value = self.accessor(row) if self.accessor is not None else row.get(self.key, "")
        return str(self.formatter(value)) if self.formatter is not None else str(value)


@dataclass(frozen=True, slots=True)
class TableStyle:
    """Reusable visual rules for a family of tables."""

    header_height: float = 34.0
    row_height: float = 30.0
    padding_x: float = 10.0
    padding_y: float = 6.0
    line_height_ratio: float = 1.25
    header_fill: ProcessColor = field(default_factory=lambda: Color(0.08, 0.16, 0.28))
    body_fill: ProcessColor = field(default_factory=lambda: Color(1.0, 1.0, 1.0))
    alternate_fill: ProcessColor | None = field(default_factory=lambda: Color(0.96, 0.97, 0.98))
    variant_fills: Mapping[str, ProcessColor] = field(default_factory=dict)
    header_text_color: ProcessColor = field(default_factory=lambda: Color(1.0, 1.0, 1.0))
    body_text_color: ProcessColor = field(default_factory=lambda: Color(0.12, 0.15, 0.2))
    variant_text_colors: Mapping[str, ProcessColor] = field(default_factory=dict)
    border_color: ProcessColor = field(default_factory=lambda: Color(0.72, 0.75, 0.8))
    border_width: float = 0.75
    header_font: FontSpec = field(default_factory=lambda: FontSpec("Helvetica-Bold"))
    body_font: FontSpec = field(default_factory=lambda: FontSpec("Helvetica"))
    header_tracking: float = 0.0
    body_tracking: float = 0.0
    header_font_size: float = 11.0
    body_font_size: float = 10.0

    def __post_init__(self) -> None:
        positive = (
            self.header_height,
            self.row_height,
            self.header_font_size,
            self.body_font_size,
            self.line_height_ratio,
        )
        if not all(value > 0 for value in positive):
            raise ValueError("Table heights and font sizes must be positive")
        if self.padding_x < 0 or self.padding_y < 0 or self.border_width < 0:
            raise ValueError("Table padding and border width must not be negative")
        if not all(math.isfinite(value) for value in (self.header_tracking, self.body_tracking)):
            raise ValueError("Table tracking must be finite")


@dataclass(slots=True)
class Table:
    """Meaningful rows and columns that deterministically render to editable art."""

    id: str
    columns: Sequence[TableColumn]
    rows: Sequence[Mapping[str, Any]]
    style: TableStyle = field(default_factory=TableStyle)
    variant_key: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("A table id must not be empty")
        if not self.columns:
            raise ValueError("A table needs at least one column")
        keys = [column.key for column in self.columns]
        if len(set(keys)) != len(keys):
            raise ValueError("Table column keys must be unique")

    @property
    def width(self) -> float:
        return sum(column.width for column in self.columns)

    def _layout(self) -> _TableLayout:
        def lines_for(column: TableColumn, value: str, font_size: float) -> tuple[str, ...]:
            if not column.wrap:
                return tuple(value.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
            return wrap_text_approximately(
                value,
                max_width=max(column.width - 2 * self.style.padding_x, 1.0),
                font_size=font_size,
            )

        def required_height(lines: Sequence[Sequence[str]], size: float) -> float:
            count = max((len(cell) for cell in lines), default=1)
            content = size + (count - 1) * size * self.style.line_height_ratio
            return content + 2 * self.style.padding_y

        header_lines = tuple(
            lines_for(column, column.title, self.style.header_font_size) for column in self.columns
        )
        header_height = max(
            self.style.header_height,
            required_height(header_lines, self.style.header_font_size),
        )
        row_lines = tuple(
            tuple(
                lines_for(column, column.text_for(row), self.style.body_font_size)
                for column in self.columns
            )
            for row in self.rows
        )
        row_heights = tuple(
            max(self.style.row_height, required_height(lines, self.style.body_font_size))
            for lines in row_lines
        )
        return _TableLayout(header_lines, header_height, row_lines, row_heights)

    @property
    def height(self) -> float:
        layout = self._layout()
        return layout.header_height + sum(layout.row_heights)

    def render(self, *, x: float, top: float) -> RenderedComponent:
        """Compile the table into composable paths and point text."""

        layout = self._layout()
        paths: list[Path] = []
        text_frames: list[TextFrame] = []
        order: list[LayerItemRef] = []

        def rectangle(item_id: str, row_top: float, height: float, fill: ProcessColor) -> None:
            path = Path(
                id=item_id,
                name=item_id,
                points=[
                    Point(x, row_top - height),
                    Point(x + self.width, row_top - height),
                    Point(x + self.width, row_top),
                    Point(x, row_top),
                ],
                fill=fill,
                stroke=None,
            )
            paths.append(path)
            order.append(LayerItemRef("path", path.id))

        rectangle(f"{self.id}.background.header", top, layout.header_height, self.style.header_fill)
        row_tops: list[float] = []
        row_top = top - layout.header_height
        for row_index, row in enumerate(self.rows):
            row_tops.append(row_top)
            variant = str(row.get(self.variant_key, "")) if self.variant_key else ""
            fill = self.style.variant_fills.get(variant)
            if fill is None:
                fill = (
                    self.style.alternate_fill
                    if row_index % 2 and self.style.alternate_fill is not None
                    else self.style.body_fill
                )
            rectangle(
                f"{self.id}.background.row-{row_index}",
                row_top,
                layout.row_heights[row_index],
                fill,
            )
            row_top -= layout.row_heights[row_index]

        horizontal_positions = [
            top,
            top - layout.header_height,
            *(row_top - layout.row_heights[index] for index, row_top in enumerate(row_tops)),
        ]
        for line_index, line_y in enumerate(horizontal_positions):
            line = Path(
                id=f"{self.id}.grid.horizontal-{line_index}",
                points=[Point(x, line_y), Point(x + self.width, line_y)],
                closed=False,
                fill=None,
                stroke=self.style.border_color,
                stroke_width=self.style.border_width,
            )
            paths.append(line)
            order.append(LayerItemRef("path", line.id))

        column_edges = [x]
        for column in self.columns:
            column_edges.append(column_edges[-1] + column.width)
        for line_index, line_x in enumerate(column_edges):
            line = Path(
                id=f"{self.id}.grid.vertical-{line_index}",
                points=[
                    Point(line_x, top),
                    Point(line_x, top - layout.header_height - sum(layout.row_heights)),
                ],
                closed=False,
                fill=None,
                stroke=self.style.border_color,
                stroke_width=self.style.border_width,
            )
            paths.append(line)
            order.append(LayerItemRef("path", line.id))

        def text_x(column_index: int, alignment: str) -> float:
            left = column_edges[column_index]
            right = column_edges[column_index + 1]
            if alignment == "right":
                return right - self.style.padding_x
            if alignment == "center":
                return (left + right) / 2
            return left + self.style.padding_x

        def baselines(
            row_top: float, height: float, size: float, line_count: int
        ) -> tuple[float, ...]:
            line_height = size * self.style.line_height_ratio
            content_height = size + (line_count - 1) * line_height
            first = row_top - (height - content_height) / 2 - size * 0.8
            return tuple(first - index * line_height for index in range(line_count))

        def add_text(
            *,
            item_id: str,
            name: str,
            value: str,
            x_position: float,
            y_position: float,
            size: float,
            font: FontSpec,
            tracking: float,
            fill: ProcessColor,
            alignment: str,
        ) -> None:
            text = TextFrame(
                id=item_id,
                name=name,
                text=value,
                x=x_position,
                y=y_position,
                font_size=size,
                font_name=font.postscript_name,
                tracking=tracking,
                fill=fill,
                alignment=alignment,
            )
            text_frames.append(text)
            order.append(LayerItemRef("text", text.id))

        for column_index, column in enumerate(self.columns):
            lines = layout.header_lines[column_index]
            line_baselines = baselines(
                top, layout.header_height, self.style.header_font_size, len(lines)
            )
            for line_index, (value, line_y) in enumerate(zip(lines, line_baselines, strict=True)):
                suffix = f".line-{line_index}" if len(lines) > 1 else ""
                add_text(
                    item_id=f"{self.id}.header.{column.key}{suffix}",
                    name=f"Header: {column.title}",
                    value=value,
                    x_position=text_x(column_index, column.alignment),
                    y_position=line_y,
                    size=self.style.header_font_size,
                    font=self.style.header_font,
                    tracking=self.style.header_tracking,
                    fill=self.style.header_text_color,
                    alignment=column.alignment,
                )

        for row_index, row in enumerate(self.rows):
            variant = str(row.get(self.variant_key, "")) if self.variant_key else ""
            color = self.style.variant_text_colors.get(variant, self.style.body_text_color)
            for column_index, column in enumerate(self.columns):
                lines = layout.row_lines[row_index][column_index]
                line_baselines = baselines(
                    row_tops[row_index],
                    layout.row_heights[row_index],
                    self.style.body_font_size,
                    len(lines),
                )
                for line_index, (value, line_y) in enumerate(
                    zip(lines, line_baselines, strict=True)
                ):
                    suffix = f".line-{line_index}" if len(lines) > 1 else ""
                    add_text(
                        item_id=f"{self.id}.row-{row_index}.{column.key}{suffix}",
                        name=f"Row {row_index + 1}: {column.title}",
                        value=value,
                        x_position=text_x(column_index, column.alignment),
                        y_position=line_y,
                        size=self.style.body_font_size,
                        font=self.style.body_font,
                        tracking=self.style.body_tracking,
                        fill=color,
                        alignment=column.alignment,
                    )

        return RenderedComponent(
            width=self.width,
            height=self.height,
            paths=paths,
            text_frames=text_frames,
            item_order=order,
        )

    def render_layer(
        self,
        *,
        x: float,
        top: float,
        layer_id: str | None = None,
        layer_name: str = "Table",
    ) -> Layer:
        """Compile the table into a standalone editable IR layer."""

        return self.render(x=x, top=top).as_layer(
            layer_id=layer_id or f"{self.id}.layer",
            layer_name=layer_name,
        )
