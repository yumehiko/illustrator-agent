"""Deterministic approximate text measurement and wrapping."""

from __future__ import annotations

from unicodedata import east_asian_width


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


def estimate_text_width(value: str, font_size: float) -> float:
    """Estimate width without consulting a font engine.

    This deterministic heuristic is suitable for provisional wrapping only. It
    is not an exact font metric or an overflow/editability acceptance result.
    """

    if font_size <= 0:
        raise ValueError("font_size must be positive")
    return sum(_character_width_units(character) for character in value) * font_size


def wrap_text_approximately(
    value: str, *, max_width: float, font_size: float
) -> tuple[str, ...]:
    """Greedily wrap text using the deterministic width heuristic."""

    if max_width <= 0:
        raise ValueError("max_width must be positive")
    lines: list[str] = []
    for paragraph in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for character in paragraph:
            candidate = current + character
            if not current or estimate_text_width(candidate, font_size) <= max_width:
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
