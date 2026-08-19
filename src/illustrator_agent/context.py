"""Explicit document and theme context for deterministic design rendering."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, ClassVar, Literal, TypeVar

from py_ai_illustrator.model import (
    Artboard,
    CmykColor,
    Color,
    Document,
    Layer,
    ProcessColor,
)

from .typography import TextStyle

_T = TypeVar("_T")


def _freeze_roles(
    values: Mapping[str, _T],
    *,
    label: str,
    expected_type: type | tuple[type, ...],
) -> Mapping[str, _T]:
    copied = dict(values)
    invalid_names = [
        name
        for name in copied
        if not isinstance(name, str) or not name or name != name.strip()
    ]
    if invalid_names:
        raise ValueError(
            f"{label} role names must be non-empty strings without surrounding whitespace"
        )
    if any(not isinstance(value, expected_type) for value in copied.values()):
        raise TypeError(f"{label} roles contain an unsupported value")
    return MappingProxyType(copied)


def _freeze_metadata(value: Any, *, path: str = "metadata") -> Any:
    if isinstance(value, Mapping):
        if any(
            not isinstance(key, str) or not key or key != key.strip()
            for key in value
        ):
            raise ValueError(f"{path} keys must be non-empty strings")
        return MappingProxyType(
            {
                key: _freeze_metadata(item, path=f"{path}.{key}")
                for key, item in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_metadata(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} numbers must be finite")
        return value
    raise TypeError(f"{path} contains a non-JSON value")


def _thaw_metadata(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_metadata(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_metadata(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class DesignTheme:
    """Immutable named paint and typography roles used by components."""

    colors: Mapping[str, ProcessColor]
    text_styles: Mapping[str, TextStyle]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "colors",
            _freeze_roles(
                self.colors,
                label="color",
                expected_type=(Color, CmykColor),
            ),
        )
        object.__setattr__(
            self,
            "text_styles",
            _freeze_roles(
                self.text_styles,
                label="text style",
                expected_type=TextStyle,
            ),
        )

    def color(self, role: str) -> ProcessColor:
        """Resolve a required color role or reject the incomplete theme."""

        try:
            return self.colors[role]
        except KeyError as error:
            available = ", ".join(sorted(self.colors)) or "none"
            raise KeyError(f"Unknown color role {role!r}; available: {available}") from error

    def text_style(self, role: str) -> TextStyle:
        """Resolve a required typography role or reject the incomplete theme."""

        try:
            return self.text_styles[role]
        except KeyError as error:
            available = ", ".join(sorted(self.text_styles)) or "none"
            raise KeyError(f"Unknown text style role {role!r}; available: {available}") from error


@dataclass(frozen=True, slots=True)
class DocumentContext:
    """Canvas, theme, unit, and provenance required to create one document."""

    width: float
    height: float
    title: str
    theme: DesignTheme
    metadata: Mapping[str, Any] = field(default_factory=dict)
    unit: ClassVar[Literal["pt"]] = "pt"

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) and value > 0 for value in (self.width, self.height)):
            raise ValueError("Document context dimensions must be finite and positive")
        if not self.title or self.title != self.title.strip():
            raise ValueError(
                "Document context title must not be empty or contain surrounding whitespace"
            )
        if not isinstance(self.theme, DesignTheme):
            raise TypeError("Document context theme must be a DesignTheme")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def create_document(
        self,
        layers: Sequence[Layer],
        *,
        artboards: Sequence[Artboard] = (),
    ) -> Document:
        """Create a low-level document without leaking mutable context state."""

        if any(not isinstance(layer, Layer) for layer in layers):
            raise TypeError("Document context layers must contain Layer values")
        if any(not isinstance(artboard, Artboard) for artboard in artboards):
            raise TypeError("Document context artboards must contain Artboard values")

        return Document(
            width=self.width,
            height=self.height,
            title=self.title,
            metadata=_thaw_metadata(self.metadata),
            layers=list(layers),
            artboards=list(artboards),
        )
