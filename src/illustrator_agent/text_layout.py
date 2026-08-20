"""Text measurement provenance, provisional wrapping, and overflow policy."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol
from unicodedata import east_asian_width


class OverflowPolicy(StrEnum):
    """Whether unverified approximate measurements may be rendered."""

    PROVISIONAL = "provisional"
    FAIL_CLOSED = "fail-closed"


class OverflowStatus(StrEnum):
    """What one measurement can establish about a width constraint."""

    VERIFIED_FIT = "verified-fit"
    OVERFLOW = "overflow"
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class TextMeasureRequest:
    """The complete typography input to one width measurement."""

    value: str
    font_postscript_name: str
    font_size: float
    tracking: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Text measurement value must be a string")
        if not self.font_postscript_name or any(
            character.isspace() for character in self.font_postscript_name
        ):
            raise ValueError("font_postscript_name must be a non-empty PostScript name")
        if not math.isfinite(self.font_size) or self.font_size <= 0:
            raise ValueError("font_size must be finite and positive")
        if not math.isfinite(self.tracking):
            raise ValueError("tracking must be finite")

    def to_dict(self) -> dict[str, str | float]:
        return {
            "value": self.value,
            "font_postscript_name": self.font_postscript_name,
            "font_size": self.font_size,
            "tracking": self.tracking,
        }


@dataclass(frozen=True, slots=True)
class MeasurementProvenance:
    """Identity and capability of the system that produced a measurement."""

    method: str
    font_aware: bool
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.method or self.method != self.method.strip():
            raise ValueError("Measurement method must not be empty")
        if type(self.font_aware) is not bool:
            raise TypeError("font_aware must be a boolean")
        if self.source is not None and (
            not self.source or self.source != self.source.strip()
        ):
            raise ValueError("Measurement source must not be empty")

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "method": self.method,
            "font_aware": self.font_aware,
            "source": self.source,
        }


APPROXIMATE_PROVENANCE = MeasurementProvenance(
    method="unicode-width-heuristic-v1",
    font_aware=False,
    source="illustrator-agent",
)


@dataclass(frozen=True, slots=True)
class TextMeasurement:
    """A measured width tied to its exact typography request and provenance."""

    request: TextMeasureRequest
    width: float
    provenance: MeasurementProvenance

    def __post_init__(self) -> None:
        if not math.isfinite(self.width) or self.width < 0:
            raise ValueError("Measured text width must be finite and non-negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "request": self.request.to_dict(),
            "width": self.width,
            "provenance": self.provenance.to_dict(),
        }


class TextMeasurer(Protocol):
    """A Layer 2 boundary for externally implemented text measurement."""

    def measure(self, request: TextMeasureRequest) -> TextMeasurement: ...


class MissingTextMeasurementError(ValueError):
    """Raised when fail-closed layout lacks a measurement for an exact request."""


@dataclass(frozen=True, slots=True)
class RecordedTextMeasurer:
    """Replay external measurements without implementing a font engine here."""

    measurements: Sequence[TextMeasurement]
    _by_request: Mapping[TextMeasureRequest, TextMeasurement] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        by_request: dict[TextMeasureRequest, TextMeasurement] = {}
        for measurement in self.measurements:
            if measurement.request in by_request:
                raise ValueError("Recorded text measurement requests must be unique")
            by_request[measurement.request] = measurement
        object.__setattr__(self, "measurements", tuple(self.measurements))
        object.__setattr__(self, "_by_request", MappingProxyType(by_request))

    def measure(self, request: TextMeasureRequest) -> TextMeasurement:
        try:
            return self._by_request[request]
        except KeyError as error:
            raise MissingTextMeasurementError(
                "No recorded measurement matches text, PostScript font, size, and tracking"
            ) from error


def _character_width_units(character: str) -> float:
    if east_asian_width(character) in {"F", "W"}:
        return 1.0
    if character in " .,:;!|'`ijlItfr()[]":
        return 0.3
    if character in "MW@%&QG":
        return 0.85
    if character.isupper():
        return 0.67
    if character.isdigit() or character in "$+-=/":
        return 0.56
    return 0.52


def estimate_text_width(value: str, font_size: float, *, tracking: float = 0.0) -> float:
    """Estimate width without consulting a font engine.

    This deterministic heuristic is suitable for provisional wrapping only. It
    is not a font-aware metric or an overflow/editability acceptance result.
    Tracking follows Illustrator's thousandths-of-an-em convention.
    """

    if not math.isfinite(font_size) or font_size <= 0:
        raise ValueError("font_size must be finite and positive")
    if not math.isfinite(tracking):
        raise ValueError("tracking must be finite")
    glyph_width = sum(_character_width_units(character) for character in value) * font_size
    tracking_width = max(len(value) - 1, 0) * font_size * tracking / 1000
    return max(glyph_width + tracking_width, 0.0)


@dataclass(frozen=True, slots=True)
class ApproximateTextMeasurer:
    """Deterministic font-independent measurement for provisional layout."""

    provenance: MeasurementProvenance = APPROXIMATE_PROVENANCE

    def __post_init__(self) -> None:
        if self.provenance.font_aware:
            raise ValueError("ApproximateTextMeasurer provenance must not be font-aware")

    def measure(self, request: TextMeasureRequest) -> TextMeasurement:
        return TextMeasurement(
            request=request,
            width=estimate_text_width(
                request.value,
                request.font_size,
                tracking=request.tracking,
            ),
            provenance=self.provenance,
        )


def wrap_text_approximately(
    value: str,
    *,
    max_width: float,
    font_size: float,
    tracking: float = 0.0,
) -> tuple[str, ...]:
    """Greedily wrap text using the deterministic font-independent heuristic."""

    if not math.isfinite(max_width) or max_width <= 0:
        raise ValueError("max_width must be finite and positive")
    lines: list[str] = []
    for paragraph in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for character in paragraph:
            candidate = current + character
            if (
                not current
                or estimate_text_width(candidate, font_size, tracking=tracking) <= max_width
            ):
                current = candidate
                continue
            break_at = current.rfind(" ")
            if break_at >= 0:
                line = current[:break_at].rstrip()
                remainder = current[break_at + 1 :].lstrip() + character
                if line:
                    lines.append(line)
                    current = remainder
                    continue
            lines.append(current.rstrip())
            current = character.lstrip() if character.isspace() else character
        lines.append(current.rstrip())
    return tuple(lines or [""])


@dataclass(frozen=True, slots=True)
class TextLineLayout:
    """One provisional line and its independently evaluated overflow status."""

    measurement: TextMeasurement
    max_width: float
    status: OverflowStatus

    def to_dict(self) -> dict[str, object]:
        return {
            "measurement": self.measurement.to_dict(),
            "max_width": self.max_width,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class TextLayoutResult:
    """Line breaks plus enough evidence to enforce an overflow policy."""

    policy: OverflowPolicy
    line_layouts: tuple[TextLineLayout, ...]
    provisional_wrap_width: float

    @property
    def lines(self) -> tuple[str, ...]:
        return tuple(line.measurement.request.value for line in self.line_layouts)

    @property
    def status(self) -> str:
        statuses = {line.status for line in self.line_layouts}
        if OverflowStatus.OVERFLOW in statuses:
            return "rejected-overflow"
        if OverflowStatus.UNVERIFIED in statuses:
            return (
                "provisional"
                if self.policy is OverflowPolicy.PROVISIONAL
                else "rejected-unverified"
            )
        return OverflowStatus.VERIFIED_FIT.value

    @property
    def renderable(self) -> bool:
        return self.status in {OverflowStatus.VERIFIED_FIT.value, "provisional"}

    @property
    def font_postscript_names(self) -> tuple[str, ...]:
        return tuple(
            sorted({line.measurement.request.font_postscript_name for line in self.line_layouts})
        )

    def require_renderable(self) -> None:
        if not self.renderable:
            raise TextOverflowError(self)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "policy": self.policy.value,
            "provisional_wrap_width": self.provisional_wrap_width,
            "font_postscript_names": list(self.font_postscript_names),
            "lines": [line.to_dict() for line in self.line_layouts],
        }


class TextOverflowError(ValueError):
    """A rejected text layout, retaining the complete decision evidence."""

    def __init__(self, result: TextLayoutResult) -> None:
        self.result = result
        super().__init__(f"Text layout rejected by {result.policy.value} policy: {result.status}")


def evaluate_text_layout(
    value: str,
    *,
    max_width: float,
    font_postscript_name: str,
    font_size: float,
    tracking: float = 0.0,
    wrap: bool = True,
    provisional_wrap_width: float | None = None,
    measurer: TextMeasurer | None = None,
    policy: OverflowPolicy = OverflowPolicy.PROVISIONAL,
) -> TextLayoutResult:
    """Wrap provisionally, then evaluate every final line with explicit provenance."""

    if not math.isfinite(max_width) or max_width <= 0:
        raise ValueError("max_width must be finite and positive")
    if not isinstance(policy, OverflowPolicy):
        raise TypeError("policy must be an OverflowPolicy")
    effective_wrap_width = (
        max_width if provisional_wrap_width is None else provisional_wrap_width
    )
    if (
        not math.isfinite(effective_wrap_width)
        or effective_wrap_width <= 0
        or effective_wrap_width > max_width
    ):
        raise ValueError("provisional_wrap_width must be positive and at most max_width")
    lines = (
        wrap_text_approximately(
            value,
            max_width=effective_wrap_width,
            font_size=font_size,
            tracking=tracking,
        )
        if wrap
        else tuple(value.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    )
    effective_measurer = measurer or ApproximateTextMeasurer()
    evaluated: list[TextLineLayout] = []
    for line in lines:
        request = TextMeasureRequest(
            value=line,
            font_postscript_name=font_postscript_name,
            font_size=font_size,
            tracking=tracking,
        )
        measurement = effective_measurer.measure(request)
        if measurement.request != request:
            raise ValueError("Text measurer returned evidence for a different request")
        if measurement.width > max_width:
            status = OverflowStatus.OVERFLOW
        elif measurement.provenance.font_aware:
            status = OverflowStatus.VERIFIED_FIT
        else:
            status = OverflowStatus.UNVERIFIED
        evaluated.append(TextLineLayout(measurement, max_width, status))
    return TextLayoutResult(
        policy=policy,
        line_layouts=tuple(evaluated),
        provisional_wrap_width=effective_wrap_width,
    )
