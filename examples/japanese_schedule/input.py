"""Explicit content and recorded measurement contract for the Japanese schedule."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from illustrator_agent import (
    MeasurementProvenance,
    RecordedTextMeasurer,
    TextMeasurement,
    TextMeasureRequest,
    array_contract,
    boolean,
    field,
    finite_number,
    non_empty_string,
    object_contract,
)

DEFAULT_INPUT = Path(__file__).parents[1] / "japanese-schedule.json"


@dataclass(frozen=True, slots=True)
class ScheduleRow:
    time: str
    category: str
    description: str
    kind: str = "standard"


@dataclass(frozen=True, slots=True)
class ScheduleFont:
    postscript_name: str
    family: str
    style: str
    header_size: float
    body_size: float
    header_tracking: float
    body_tracking: float


@dataclass(frozen=True, slots=True)
class RecordedMeasurement:
    text: str
    font_postscript_name: str
    font_size: float
    tracking: float
    width: float


@dataclass(frozen=True, slots=True)
class JapaneseScheduleInput:
    title: str
    font: ScheduleFont
    rows: tuple[ScheduleRow, ...]
    measurement_provenance: MeasurementProvenance
    measurements: tuple[RecordedMeasurement, ...]

    def recorded_measurer(self) -> RecordedTextMeasurer:
        provenance = self.measurement_provenance
        return RecordedTextMeasurer(
            tuple(
                TextMeasurement(
                    request=TextMeasureRequest(
                        value=measurement.text,
                        font_postscript_name=measurement.font_postscript_name,
                        font_size=measurement.font_size,
                        tracking=measurement.tracking,
                    ),
                    width=measurement.width,
                    provenance=provenance,
                )
                for measurement in self.measurements
            )
        )


_bounded_text = non_empty_string().refine(
    lambda value: len(value) <= 80,
    "must contain at most 80 characters",
)

_postscript_name = non_empty_string().refine(
    lambda value: not any(character.isspace() for character in value),
    "must be a PostScript font name without whitespace",
)

_row_contract = object_contract(
    {
        "time": non_empty_string().refine(
            lambda value: len(value) <= 8,
            "must contain at most 8 characters",
        ),
        "category": non_empty_string().refine(
            lambda value: len(value) <= 16,
            "must contain at most 16 characters",
        ),
        "description": _bounded_text,
        "kind": field(non_empty_string(), default="standard"),
    }
).map(lambda values: ScheduleRow(**values))

_font_contract = object_contract(
    {
        "postscript_name": _postscript_name,
        "family": non_empty_string(),
        "style": non_empty_string(),
        "header_size": finite_number().refine(lambda value: value > 0, "must be positive"),
        "body_size": finite_number().refine(lambda value: value > 0, "must be positive"),
        "header_tracking": finite_number(),
        "body_tracking": finite_number(),
    }
).map(lambda values: ScheduleFont(**values))

_provenance_contract = object_contract(
    {
        "method": non_empty_string(),
        "font_aware": boolean(),
        "source": non_empty_string(),
    }
).map(lambda values: MeasurementProvenance(**values))

_measurement_contract = object_contract(
    {
        "text": non_empty_string(),
        "font_postscript_name": _postscript_name,
        "font_size": finite_number().refine(lambda value: value > 0, "must be positive"),
        "tracking": finite_number(),
        "width": finite_number().refine(lambda value: value >= 0, "must not be negative"),
    }
).map(lambda values: RecordedMeasurement(**values))

_schedule_contract = (
    object_contract(
        {
            "title": non_empty_string(),
            "font": _font_contract,
            "rows": array_contract(_row_contract).refine(
                lambda rows: 1 <= len(rows) <= 8,
                "must contain between 1 and 8 rows",
            ),
            "measurement_provenance": _provenance_contract,
            "measurements": array_contract(_measurement_contract).refine(
                lambda measurements: bool(measurements),
                "must contain recorded measurements",
            ),
        }
    )
    .refine(
        lambda values: all(
            measurement.font_postscript_name == values["font"].postscript_name
            and (
                (
                    measurement.font_size == values["font"].header_size
                    and measurement.tracking == values["font"].header_tracking
                )
                or (
                    measurement.font_size == values["font"].body_size
                    and measurement.tracking == values["font"].body_tracking
                )
            )
            for measurement in values["measurements"]
        ),
        "measurements must use the declared font, sizes, and tracking",
    )
    .map(lambda values: JapaneseScheduleInput(**values))
)


def load_schedule_input(path: str | Path = DEFAULT_INPUT) -> JapaneseScheduleInput:
    """Load content and external font measurement evidence from explicit JSON."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return _schedule_contract.validate(raw)
