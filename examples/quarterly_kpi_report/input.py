"""Input schema and validation for the quarterly KPI report."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    """Load and validate the explicit production input."""

    raw = _mapping(json.loads(Path(path).read_text(encoding="utf-8")), name="report input")
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
