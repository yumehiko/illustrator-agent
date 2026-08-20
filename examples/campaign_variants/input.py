"""Explicit input schema for the campaign variant production."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from illustrator_agent import (
    array_contract,
    finite_number,
    non_empty_string,
    object_contract,
    validate_identity_segment,
)

DEFAULT_INPUT = Path(__file__).parents[1] / "campaign-variants.json"
LAYOUTS = frozenset({"square", "portrait", "banner"})


@dataclass(frozen=True, slots=True)
class VariantSpec:
    key: str
    name: str
    left: float
    top: float
    width: float
    height: float
    layout: str

    def __post_init__(self) -> None:
        validate_identity_segment(self.key)
        if not self.name or self.name != self.name.strip():
            raise ValueError("Variant name must not be empty or contain surrounding whitespace")
        if self.layout not in LAYOUTS:
            raise ValueError(f"Variant layout must be one of {sorted(LAYOUTS)!r}")
        values = (self.left, self.top, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Variant bounds must be finite")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Variant dimensions must be positive")


@dataclass(frozen=True, slots=True)
class CampaignInput:
    width: float
    height: float
    title: str
    eyebrow: str
    description: str
    action: str
    variants: tuple[VariantSpec, ...]

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) and value > 0 for value in (self.width, self.height)):
            raise ValueError("Campaign canvas dimensions must be finite and positive")
        if not all((self.title, self.eyebrow, self.description, self.action)):
            raise ValueError("Campaign text fields must not be empty")
        title_lines = self.title.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if len(title_lines) != 2 or not all(title_lines):
            raise ValueError("Campaign title must contain exactly two non-empty lines")
        if any("\n" in value or "\r" in value for value in (self.eyebrow, self.action)):
            raise ValueError("Campaign eyebrow and action must each contain one line")
        if not self.variants:
            raise ValueError("Campaign must contain at least one variant")
        keys = [variant.key for variant in self.variants]
        names = [variant.name for variant in self.variants]
        if len(set(keys)) != len(keys):
            raise ValueError("Variant semantic keys must be unique")
        if len(set(names)) != len(names):
            raise ValueError("Variant names must be unique")
        for variant in self.variants:
            if (
                variant.left < 0
                or variant.top > self.height
                or variant.left + variant.width > self.width
                or variant.top - variant.height < 0
            ):
                raise ValueError(f"Variant {variant.key!r} must fit inside the campaign canvas")


_variant_contract = object_contract(
    {
        "key": non_empty_string(),
        "name": non_empty_string(),
        "left": finite_number(),
        "top": finite_number(),
        "width": finite_number(),
        "height": finite_number(),
        "layout": non_empty_string(),
    }
).map(lambda values: VariantSpec(**values))

_campaign_contract = object_contract(
    {
        "width": finite_number(),
        "height": finite_number(),
        "title": non_empty_string(),
        "eyebrow": non_empty_string(),
        "description": non_empty_string(),
        "action": non_empty_string(),
        "variants": array_contract(_variant_contract).refine(
            lambda variants: bool(variants)
            and len({variant.key for variant in variants}) == len(variants),
            "must contain at least one variant with unique semantic keys",
        ),
    }
).map(lambda values: CampaignInput(**values))


def load_campaign_input(path: str | Path = DEFAULT_INPUT) -> CampaignInput:
    """Load and validate one explicit campaign variant input."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return _campaign_contract.validate(raw)
