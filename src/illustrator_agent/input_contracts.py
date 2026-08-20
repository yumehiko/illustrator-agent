"""Composable contracts for validating explicit external input values."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")

_Path = tuple[str | int, ...]
_MISSING = object()
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _format_path(parts: _Path) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        elif _IDENTIFIER.fullmatch(part):
            path += f".{part}"
        else:
            path += f"[{json.dumps(part, ensure_ascii=False)}]"
    return path


class InputValidationError(ValueError):
    """A validation failure with a stable path into the input value."""

    def __init__(self, parts: _Path, message: str) -> None:
        self.path = _format_path(parts)
        self.message = message
        super().__init__(f"{self.path}: {message}")


class Contract(Generic[T]):
    """Validate and convert one external Python value."""

    __slots__ = ("_validator",)

    def __init__(self, validator: Callable[[object, _Path], T]) -> None:
        self._validator = validator

    def validate(self, value: object) -> T:
        """Validate a value from the root path and return its converted form."""

        return self._validator(value, ())

    def map(self, convert: Callable[[T], U]) -> Contract[U]:
        """Convert a validated value into a domain value."""

        def validator(value: object, path: _Path) -> U:
            validated = self._validator(value, path)
            try:
                return convert(validated)
            except InputValidationError:
                raise
            except ValueError as error:
                raise InputValidationError(path, str(error)) from error

        return Contract(validator)

    def refine(self, predicate: Callable[[T], bool], message: str) -> Contract[T]:
        """Add a value or cross-field constraint at this contract's path."""

        def validator(value: object, path: _Path) -> T:
            validated = self._validator(value, path)
            if not predicate(validated):
                raise InputValidationError(path, message)
            return validated

        return Contract(validator)


@dataclass(frozen=True, slots=True)
class _Field(Generic[T]):
    contract: Contract[T]
    default: object = _MISSING


def field(contract: Contract[T], *, default: object = _MISSING) -> _Field[T]:
    """Declare an object field, optionally supplying a value when it is absent."""

    return _Field(contract, default)


def object_contract(
    fields: Mapping[str, Contract[Any] | _Field[Any]],
) -> Contract[dict[str, Any]]:
    """Validate a mapping's declared fields and return their converted values."""

    declared = {
        name: specification
        if isinstance(specification, _Field)
        else _Field(specification)
        for name, specification in fields.items()
    }

    def validator(value: object, path: _Path) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise InputValidationError(path, "must be an object")
        validated: dict[str, Any] = {}
        for name, specification in declared.items():
            field_path = (*path, name)
            if name in value:
                raw = value[name]
            elif specification.default is not _MISSING:
                raw = specification.default
            else:
                raise InputValidationError(field_path, "is required")
            validated[name] = specification.contract._validator(raw, field_path)
        return validated

    return Contract(validator)


def array_contract(item: Contract[T]) -> Contract[tuple[T, ...]]:
    """Validate a non-string sequence and return an immutable tuple."""

    def validator(value: object, path: _Path) -> tuple[T, ...]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            raise InputValidationError(path, "must be an array")
        return tuple(item._validator(member, (*path, index)) for index, member in enumerate(value))

    return Contract(validator)


def non_empty_string() -> Contract[str]:
    """Accept a string containing at least one character."""

    def validator(value: object, path: _Path) -> str:
        if not isinstance(value, str) or not value:
            raise InputValidationError(path, "must be a non-empty string")
        return value

    return Contract(validator)


def finite_number() -> Contract[float]:
    """Accept an int or float other than bool and return a finite float."""

    def validator(value: object, path: _Path) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InputValidationError(path, "must be a finite number")
        try:
            converted = float(value)
        except OverflowError as error:
            raise InputValidationError(path, "must be a finite number") from error
        if not math.isfinite(converted):
            raise InputValidationError(path, "must be a finite number")
        return converted

    return Contract(validator)


def boolean() -> Contract[bool]:
    """Accept a boolean value."""

    def validator(value: object, path: _Path) -> bool:
        if not isinstance(value, bool):
            raise InputValidationError(path, "must be a boolean")
        return value

    return Contract(validator)
