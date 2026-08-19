"""M1 reference production: an editable, data-driven quarterly KPI report."""

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from illustrator_agent import (
    Color,
    DesignTheme,
    Document,
    DocumentContext,
    LayerBuilder,
    RenderedComponent,
    TextBlock,
    TextStyle,
    ellipse_path,
    polyline_path,
    rectangle_path,
)
from illustrator_agent.production import ProductionContract, run_reference_production

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "quarterly-kpi-report.json"
DEFAULT_OUTPUT = HERE.parent / "build" / "m1"


def _report_theme() -> DesignTheme:
    colors = {
        "ink": Color(0.06, 0.1, 0.18),
        "accent": Color(0.1, 0.38, 0.78),
        "danger": Color(0.92, 0.3, 0.22),
        "muted": Color(0.4, 0.44, 0.52),
        "grid": Color(0.78, 0.8, 0.84),
        "paper": Color(0.965, 0.96, 0.94),
        "surface": Color(1, 1, 1),
        "border": Color(0.82, 0.82, 0.8),
    }
    return DesignTheme(
        colors=colors,
        text_styles={
            "report-period": TextStyle(
                font_size=9,
                font_name="Helvetica-Bold",
                fill=colors["accent"],
            ),
            "report-title": TextStyle(
                font_size=24,
                font_name="Helvetica-Bold",
                fill=colors["ink"],
            ),
            "metric-label": TextStyle(
                font_size=8,
                font_name="Helvetica-Bold",
                fill=colors["muted"],
            ),
            "metric-value": TextStyle(
                font_size=22,
                font_name="Helvetica-Bold",
                fill=colors["ink"],
            ),
            "metric-change-positive": TextStyle(
                font_size=8,
                font_name="Helvetica-Bold",
                fill=colors["accent"],
            ),
            "metric-change-negative": TextStyle(
                font_size=8,
                font_name="Helvetica-Bold",
                fill=colors["danger"],
            ),
            "chart-axis": TextStyle(font_size=7, fill=colors["muted"]),
            "chart-month": TextStyle(font_size=8, fill=colors["muted"]),
            "chart-title": TextStyle(
                font_size=11,
                font_name="Helvetica-Bold",
                fill=colors["ink"],
            ),
            "chart-legend": TextStyle(
                font_size=8,
                font_name="Helvetica-Bold",
                fill=colors["danger"],
            ),
            "report-source": TextStyle(font_size=7, fill=colors["muted"]),
        },
    )


REPORT_THEME = _report_theme()
REPORT_CONTEXT = DocumentContext(
    width=612,
    height=420,
    title="Semantic quarterly KPI report",
    theme=REPORT_THEME,
    metadata={
        "source": "examples/quarterly_kpi_report.py",
        "component": "LineChart",
        "business_case": "quarterly-kpi-report",
    },
)


@dataclass(frozen=True, slots=True)
class Metric:
    label: str
    value: str
    change: str
    positive: bool = True


@dataclass(frozen=True, slots=True)
class ChartInput:
    labels: tuple[str, ...]
    values: tuple[float, ...]
    target: float


@dataclass(frozen=True, slots=True)
class ReportInput:
    period: str
    title: str
    metrics: tuple[Metric, ...]
    chart: ChartInput
    source: str
    refreshed: str

    def __post_init__(self) -> None:
        if not all((self.period, self.title, self.source, self.refreshed)):
            raise ValueError("Report text fields must not be empty")
        if len(self.metrics) != 3:
            raise ValueError("The M1 report layout requires exactly three metrics")
        if any(
            not metric.label or not metric.value or not metric.change
            for metric in self.metrics
        ):
            raise ValueError("Metric label, value, and change must not be empty")
        if len(self.chart.labels) != len(self.chart.values) or len(self.chart.values) < 2:
            raise ValueError("Chart labels and values must match and contain at least two points")
        if any(not label for label in self.chart.labels):
            raise ValueError("Chart labels must not be empty")
        if not all(math.isfinite(value) for value in (*self.chart.values, self.chart.target)):
            raise ValueError("Chart values and target must be finite")


def _mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _sequence(value: Any, *, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an array")
    return value


def _string(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _number(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _boolean(value: Any, *, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def load_report_input(path: str | Path = DEFAULT_INPUT) -> ReportInput:
    """Load and validate the explicit input used by the M1 production."""

    source = Path(path)
    raw = _mapping(json.loads(source.read_text(encoding="utf-8")), name="report input")
    metrics = tuple(
        Metric(
            label=_string(item.get("label"), name="metric.label"),
            value=_string(item.get("value"), name="metric.value"),
            change=_string(item.get("change"), name="metric.change"),
            positive=_boolean(item.get("positive", True), name="metric.positive"),
        )
        for value in _sequence(raw.get("metrics"), name="metrics")
        for item in [_mapping(value, name="metric")]
    )
    chart = _mapping(raw.get("chart"), name="chart")
    labels = tuple(
        _string(value, name="chart label")
        for value in _sequence(chart.get("labels"), name="chart.labels")
    )
    values = tuple(
        _number(value, name="chart value")
        for value in _sequence(chart.get("values"), name="chart.values")
    )
    return ReportInput(
        period=_string(raw.get("period"), name="period"),
        title=_string(raw.get("title"), name="title"),
        metrics=metrics,
        chart=ChartInput(
            labels=labels,
            values=values,
            target=_number(chart.get("target"), name="chart.target"),
        ),
        source=_string(raw.get("source"), name="source"),
        refreshed=_string(raw.get("refreshed"), name="refreshed"),
    )


@dataclass(frozen=True, slots=True)
class MetricCard:
    id: str
    metric: Metric
    theme: DesignTheme = REPORT_THEME
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
    theme: DesignTheme = REPORT_THEME
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
        ticks = (60, 80, 100, 120)
        for tick in ticks:
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


def build_document(
    report: ReportInput | None = None,
    *,
    context: DocumentContext = REPORT_CONTEXT,
) -> Document:
    report = report or load_report_input()
    theme = context.theme
    builder = LayerBuilder(id="quarterly-report", name="Quarterly KPI report")
    builder.add_path(
        rectangle_path(
            "report.background",
            x=0,
            top=context.height,
            width=context.width,
            height=context.height,
            fill=theme.color("paper"),
            name="Report background",
        )
    )
    builder.add(
        TextBlock(
            id="report.eyebrow",
            name="Report period",
            text=report.period,
            width=536,
            alignment="right",
            wrap=False,
            style=theme.text_style("report-period"),
        ).render(x=38, top=394)
    )
    builder.add(
        TextBlock(
            id="report.title",
            name="Report title",
            text=report.title,
            width=536,
            wrap=False,
            style=theme.text_style("report-title"),
        ).render(x=38, top=377)
    )

    for index, (metric, x) in enumerate(
        zip(report.metrics, (38, 224, 410), strict=True), start=1
    ):
        card = MetricCard(id=f"metric-{index}", metric=metric, theme=theme)
        builder.add_grouped(
            card.render(x=x, top=332),
            group_id=f"metric-{index}.group",
            group_name=f"Metric: {metric.label}",
        )

    builder.add_path(
        rectangle_path(
            "chart.panel",
            x=38,
            top=244,
            width=536,
            height=194,
            fill=theme.color("surface"),
            stroke=theme.color("border"),
            stroke_width=0.7,
            name="Chart panel",
        )
    )
    builder.add(
        TextBlock(
            id="chart.title",
            name="Chart title",
            text="Monthly operating index",
            width=250,
            wrap=False,
            style=theme.text_style("chart-title"),
        ).render(x=58, top=224)
    )
    builder.add(
        TextBlock(
            id="chart.legend",
            name="Target legend",
            text="TARGET 100",
            width=120,
            alignment="right",
            wrap=False,
            style=theme.text_style("chart-legend"),
        ).render(x=434, top=223)
    )
    chart = LineChart(
        id="operating-index",
        labels=report.chart.labels,
        values=report.chart.values,
        target=report.chart.target,
        theme=theme,
    )
    builder.add_grouped(
        chart.render(x=94, top=195),
        group_id="operating-index.group",
        group_name="Operating index chart",
    )
    builder.add(
        TextBlock(
            id="report.source",
            name="Data source",
            text=f"Source: {report.source} / refreshed {report.refreshed}",
            width=536,
            alignment="right",
            wrap=False,
            style=theme.text_style("report-source"),
        ).render(x=38, top=30)
    )
    return context.create_document([builder.build()])


M1_CONTRACT = ProductionContract(
    production_id="quarterly-kpi-report",
    width=REPORT_CONTEXT.width,
    height=REPORT_CONTEXT.height,
    layer_names=("Quarterly KPI report",),
    path_count=17,
    text_count=24,
    group_count=4,
    required_ids=(
        "quarterly-report",
        "metric-1.group",
        "metric-2.group",
        "metric-3.group",
        "operating-index.group",
        "operating-index.actual",
        "operating-index.target",
        "report.title.line-0",
    ),
    required_group_names=(
        "Metric: Revenue",
        "Metric: Gross margin",
        "Metric: Retention",
        "Operating index chart",
    ),
    visual_acceptance=(
        "タイトル、3つのKPIカード、折れ線チャート、出典が見切れず読める",
        "見出し、KPI値、chartのvisual hierarchyと余白が意図どおりである",
        "actual、target、gridの線種・色・重なり順が意図どおりである",
    ),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--illustrator",
        action="store_true",
        help="run Illustrator structure, native materialization, and reopen checks",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--accept-visual-by",
        help="record the human who approved the generated native preview",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    report_input = load_report_input(args.input)
    result = run_reference_production(
        lambda: build_document(report_input),
        source=__file__,
        input_data=args.input,
        output_directory=args.output_dir,
        contract=M1_CONTRACT,
        include_illustrator=args.illustrator,
        visual_accepted_by=args.accept_visual_by,
        force=args.force,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {"status": result["status"], "report": result["report_path"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["status"] == "passed" or result["status"].startswith("awaiting-") else 1


if __name__ == "__main__":
    raise SystemExit(main())
