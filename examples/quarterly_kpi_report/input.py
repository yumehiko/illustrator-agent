"""Input schema and validation for the quarterly KPI report."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from illustrator_agent import (
    array_contract,
    boolean,
    field,
    finite_number,
    non_empty_string,
    object_contract,
)

DEFAULT_INPUT = Path(__file__).parents[1] / "quarterly-kpi-report.json"


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
            raise ValueError("The reference layout requires exactly three metrics")
        if any(
            not metric.label or not metric.value or not metric.change for metric in self.metrics
        ):
            raise ValueError("Metric label, value, and change must not be empty")
        if len(self.chart.labels) != len(self.chart.values) or len(self.chart.values) < 2:
            raise ValueError("Chart labels and values must match and contain at least two points")
        if any(not label for label in self.chart.labels):
            raise ValueError("Chart labels must not be empty")
        if not all(math.isfinite(value) for value in (*self.chart.values, self.chart.target)):
            raise ValueError("Chart values and target must be finite")


_metric_contract = object_contract(
    {
        "label": non_empty_string(),
        "value": non_empty_string(),
        "change": non_empty_string(),
        "positive": field(boolean(), default=True),
    }
).map(lambda values: Metric(**values))

_chart_contract = (
    object_contract(
        {
            "labels": array_contract(non_empty_string()),
            "values": array_contract(finite_number()),
            "target": finite_number(),
        }
    )
    .refine(
        lambda values: len(values["labels"]) == len(values["values"])
        and len(values["values"]) >= 2,
        "labels and values must match and contain at least two points",
    )
    .map(lambda values: ChartInput(**values))
)

_report_contract = object_contract(
    {
        "period": non_empty_string(),
        "title": non_empty_string(),
        "metrics": array_contract(_metric_contract).refine(
            lambda metrics: len(metrics) == 3,
            "must contain exactly three metrics",
        ),
        "chart": _chart_contract,
        "source": non_empty_string(),
        "refreshed": non_empty_string(),
    }
).map(lambda values: ReportInput(**values))


def load_report_input(path: str | Path = DEFAULT_INPUT) -> ReportInput:
    """Load and validate the explicit production input."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return _report_contract.validate(raw)
