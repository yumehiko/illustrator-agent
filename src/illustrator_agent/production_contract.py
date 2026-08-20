"""Data types describing machine-checkable production contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from py_ai_illustrator.model import Document

DocumentFactory = Callable[[], Document]


@dataclass(frozen=True, slots=True)
class ProductionArtboard:
    """An artboard and the semantic group that owns its principal content."""

    id: str
    name: str
    left: float
    top: float
    width: float
    height: float
    group_id: str
    required_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtboardVariantContract:
    """Semantic component identity corresponding to one production artboard."""

    semantic_key: str
    component_id: str
    artboard_id: str


@dataclass(frozen=True, slots=True)
class ProductionLinkedImage:
    """Expected editable linked-image placement in document coordinates."""

    id: str
    source: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class ProductionAreaText:
    """Expected editable area-text geometry and typography."""

    id: str
    width: float
    height: float
    leading: float
    font_name: str


@dataclass(frozen=True, slots=True)
class ProductionContract:
    """Machine-checkable and human-checkable completion criteria."""

    production_id: str
    width: float
    height: float
    layer_names: tuple[str, ...]
    path_count: int
    text_count: int
    group_count: int
    required_ids: tuple[str, ...]
    required_group_names: tuple[str, ...]
    visual_acceptance: tuple[str, ...]
    required_fonts: tuple[str, ...] = ()
    require_verified_text_layout: bool = False
    artboards: tuple[ProductionArtboard, ...] = ()
    artboard_variants: tuple[ArtboardVariantContract, ...] = ()
    linked_images: tuple[ProductionLinkedImage, ...] = ()
    area_texts: tuple[ProductionAreaText, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.required_fonts)) != len(self.required_fonts):
            raise ValueError("Production contract required fonts must be unique")
        if any(
            not name or any(character.isspace() for character in name)
            for name in self.required_fonts
        ):
            raise ValueError("Production contract fonts must use PostScript names")
        variant_keys = [variant.semantic_key for variant in self.artboard_variants]
        if len(set(variant_keys)) != len(variant_keys):
            raise ValueError("Production contract variant semantic keys must be unique")
