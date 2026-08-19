"""Production-specific KPI card and chart components."""

from __future__ import annotations

from dataclasses import dataclass

from illustrator_agent import (
    DesignTheme,
    LayerBuilder,
    RenderedComponent,
    TextBlock,
    ellipse_path,
    polyline_path,
    rectangle_path,
)

from .input import Metric


@dataclass(frozen=True, slots=True)
class MetricCard:
    id: str
    metric: Metric
    theme: DesignTheme
    width: float = 164
    height: float = 70

    def render(self, *, x: float, top: float) -> RenderedComponent:
        builder = LayerBuilder(id=f"{self.id}.content", name=self.metric.label)
        builder.add_path(
            rectangle_path(
                f"{self.id}.background",
                x=x,
                top=top,
                width=self.width,
                height=self.height,
                fill=self.theme.color("surface"),
                stroke=self.theme.color("border"),
                stroke_width=0.7,
                name=f"Metric card: {self.metric.label}",
            )
        )
        builder.add(
            TextBlock(
                id=f"{self.id}.label",
                name="Metric label",
                text=self.metric.label.upper(),
                width=self.width - 24,
                wrap=False,
                style=self.theme.text_style("metric-label"),
            ).render(x=x + 12, top=top - 12)
        )
        builder.add(
            TextBlock(
                id=f"{self.id}.value",
                name="Metric value",
                text=self.metric.value,
                width=self.width - 24,
                alignment="right",
                wrap=False,
                style=self.theme.text_style("metric-value"),
            ).render(x=x + 12, top=top - 31)
        )
        builder.add(
            TextBlock(
                id=f"{self.id}.change",
                name="Metric change",
                text=self.metric.change,
                width=60,
                alignment="right",
                wrap=False,
                style=self.theme.text_style(
                    "metric-change-positive"
                    if self.metric.positive
                    else "metric-change-negative"
                ),
            ).render(x=x + self.width - 72, top=top - 59)
        )
        layer = builder.build()
        return RenderedComponent(
            width=self.width,
            height=self.height,
            paths=layer.paths,
            text_frames=layer.text_frames,
            item_order=layer.item_order,
        )


@dataclass(frozen=True, slots=True)
class LineChart:
    id: str
    labels: tuple[str, ...]
    values: tuple[float, ...]
    target: float
    theme: DesignTheme
    width: float = 450
    height: float = 118
    minimum: float = 60
    maximum: float = 120

    def __post_init__(self) -> None:
        if len(self.labels) != len(self.values) or len(self.values) < 2:
            raise ValueError("LineChart requires matching labels and at least two values")
        if not self.minimum < self.maximum:
            raise ValueError("LineChart maximum must be greater than minimum")
        if any(
            value < self.minimum or value > self.maximum
            for value in (*self.values, self.target)
        ):
            raise ValueError("LineChart value or target falls outside the configured scale")

    def _y(self, value: float, *, top: float) -> float:
        ratio = (value - self.minimum) / (self.maximum - self.minimum)
        return top - self.height + ratio * self.height

    def render(self, *, x: float, top: float) -> RenderedComponent:
        builder = LayerBuilder(id=f"{self.id}.content", name="Monthly performance")
        for tick in (60, 80, 100, 120):
            y = self._y(tick, top=top)
            builder.add_path(
                polyline_path(
                    f"{self.id}.grid-{tick}",
                    points=[(x, y), (x + self.width, y)],
                    stroke=self.theme.color("grid"),
                    stroke_width=0.7,
                    dash_pattern=(2, 4),
                    line_cap="round",
                    name=f"Grid line {tick}",
                )
            )
            builder.add(
                TextBlock(
                    id=f"{self.id}.tick-{tick}",
                    name="Y axis value",
                    text=str(tick),
                    width=30,
                    alignment="right",
                    wrap=False,
                    style=self.theme.text_style("chart-axis"),
                ).render(x=x - 38, top=y + 3)
            )

        target_y = self._y(self.target, top=top)
        builder.add_path(
            polyline_path(
                f"{self.id}.target",
                points=[(x, target_y), (x + self.width, target_y)],
                stroke=self.theme.color("danger"),
                stroke_width=1.6,
                dash_pattern=(10, 6),
                dash_offset=2,
                line_cap="round",
                name="Target line",
            )
        )
        step = self.width / (len(self.values) - 1)
        points = [
            (x + index * step, self._y(value, top=top))
            for index, value in enumerate(self.values)
        ]
        builder.add_path(
            polyline_path(
                f"{self.id}.actual",
                points=points,
                stroke=self.theme.color("accent"),
                stroke_width=3,
                line_cap="round",
                line_join="round",
                name="Actual performance",
            )
        )
        for index, ((point_x, point_y), label, value) in enumerate(
            zip(points, self.labels, self.values, strict=True)
        ):
            builder.add_path(
                ellipse_path(
                    f"{self.id}.point-{index}",
                    center_x=point_x,
                    center_y=point_y,
                    radius_x=4,
                    radius_y=4,
                    fill=self.theme.color("surface"),
                    stroke=self.theme.color("accent"),
                    stroke_width=2,
                    name=f"{label}: {value:g}",
                )
            )
            builder.add(
                TextBlock(
                    id=f"{self.id}.label-{index}",
                    name="Month label",
                    text=label,
                    width=50,
                    alignment="center",
                    wrap=False,
                    style=self.theme.text_style("chart-month"),
                ).render(x=point_x - 25, top=top - self.height - 12)
            )
        layer = builder.build()
        return RenderedComponent(
            width=self.width,
            height=self.height + 24,
            paths=layer.paths,
            text_frames=layer.text_frames,
            item_order=layer.item_order,
        )
