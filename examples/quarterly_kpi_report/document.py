"""Theme and document assembly for the quarterly KPI report."""

from __future__ import annotations

from pathlib import Path

from illustrator_agent import (
    Color,
    DesignTheme,
    Document,
    DocumentContext,
    FontSpec,
    LayerBuilder,
    TextBlock,
    TextStyle,
    rectangle_path,
)

from .components import LineChart, MetricCard
from .input import ReportInput, load_report_input

DOCUMENT_SOURCE = Path(__file__)


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
    bold = FontSpec("Helvetica-Bold")
    return DesignTheme(
        colors=colors,
        text_styles={
            "report-period": TextStyle(font_size=9, font=bold, fill=colors["accent"]),
            "report-title": TextStyle(font_size=24, font=bold, fill=colors["ink"]),
            "metric-label": TextStyle(font_size=8, font=bold, fill=colors["muted"]),
            "metric-value": TextStyle(font_size=22, font=bold, fill=colors["ink"]),
            "metric-change-positive": TextStyle(
                font_size=8, font=bold, fill=colors["accent"]
            ),
            "metric-change-negative": TextStyle(
                font_size=8, font=bold, fill=colors["danger"]
            ),
            "chart-axis": TextStyle(font_size=7, fill=colors["muted"]),
            "chart-month": TextStyle(font_size=8, fill=colors["muted"]),
            "chart-title": TextStyle(font_size=11, font=bold, fill=colors["ink"]),
            "chart-legend": TextStyle(font_size=8, font=bold, fill=colors["danger"]),
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
        "source": "examples/quarterly_kpi_report/document.py",
        "component": "LineChart",
        "business_case": "quarterly-kpi-report",
    },
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
