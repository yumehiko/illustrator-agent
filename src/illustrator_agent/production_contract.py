"""Pure production contracts, document evidence, and layout verification."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from py_ai_illustrator.model import Document, Group
from py_ai_illustrator.semantic import semantic_diff

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


def _document_evidence(document: Document) -> dict[str, Any]:
    groups: list[Group] = []
    paths = []
    texts = []
    images = []
    group_descendant_ids: dict[str, list[str]] = {}
    group_names_by_id: dict[str, str | None] = {}

    def visit_group(group: Group) -> list[str]:
        groups.append(group)
        paths.extend(group.paths)
        paths.extend(path for compound in group.compound_paths for path in compound.paths)
        paths.extend(
            path
            for clipping in group.clipping_groups
            for path in (clipping.clipping_path, *clipping.paths)
        )
        texts.extend(group.text_frames)
        images.extend(group.linked_images)
        descendants = [
            *(path.id for path in group.paths),
            *(text.id for text in group.text_frames),
            *(image.id for image in group.linked_images),
        ]
        for child in group.groups:
            descendants.append(child.id)
            descendants.extend(visit_group(child))
        group_descendant_ids[group.id] = descendants
        group_names_by_id[group.id] = group.name
        return descendants

    for layer in document.layers:
        paths.extend(layer.paths)
        paths.extend(path for compound in layer.compound_paths for path in compound.paths)
        paths.extend(
            path
            for clipping in layer.clipping_groups
            for path in (clipping.clipping_path, *clipping.paths)
        )
        texts.extend(layer.text_frames)
        images.extend(layer.linked_images)
        for group in layer.groups:
            visit_group(group)
    ids = {
        *(artboard.id for artboard in document.artboards),
        *(layer.id for layer in document.layers),
        *(group.id for group in groups),
        *(path.id for path in paths),
        *(text.id for text in texts),
        *(image.id for image in images),
    }
    point_text_signatures = sorted(
        (
            {
                "id": text.id,
                "text": text.text,
                "font_postscript_name": text.native_font_name or text.font_name,
                "font_size": text.font_size,
                "tracking": text.tracking,
            }
            for text in texts
            if text.area_width is None
        ),
        key=lambda signature: signature["id"],
    )
    return {
        "width": document.width,
        "height": document.height,
        "layer_names": [layer.name for layer in document.layers],
        "path_count": len(paths),
        "text_count": len(texts),
        "group_count": len(groups),
        "linked_image_count": len(images),
        "linked_images": [
            {
                "id": image.id,
                "source": image.source,
                "x": image.x,
                "y": image.y,
                "width": image.width,
                "height": image.height,
            }
            for image in images
        ],
        "area_texts": [
            {
                "id": text.id,
                "width": text.area_width,
                "height": text.area_height,
                "leading": text.leading,
                "font_name": text.native_font_name or text.font_name,
            }
            for text in texts
            if text.is_area_text
        ],
        "artboards": [
            {
                "id": artboard.id,
                "name": artboard.name,
                "left": artboard.left,
                "top": artboard.top,
                "width": artboard.width,
                "height": artboard.height,
            }
            for artboard in document.artboards
        ],
        "group_names": [group.name for group in groups],
        "group_names_by_id": group_names_by_id,
        "group_descendant_ids": group_descendant_ids,
        "font_postscript_names": sorted(
            {text.native_font_name or text.font_name for text in texts}
        ),
        "point_text_count": len(point_text_signatures),
        "point_text_signatures": point_text_signatures,
        "ids": sorted(ids),
    }


def _verified_layout_signatures(
    text_layout_report: Mapping[str, Any] | None,
) -> list[dict[str, Any]] | None:
    if text_layout_report is None or text_layout_report.get("status") != "verified-fit":
        return None
    if text_layout_report.get("policy") != "fail-closed":
        return None
    cells = text_layout_report.get("cells")
    if not isinstance(cells, list) or not cells:
        return None

    signatures: list[dict[str, Any]] = []
    for cell in cells:
        if (
            not isinstance(cell, dict)
            or cell.get("status") != "verified-fit"
            or cell.get("policy") != "fail-closed"
        ):
            return None
        lines = cell.get("lines")
        if not isinstance(lines, list) or not lines:
            return None
        for line in lines:
            if not isinstance(line, dict) or line.get("status") != "verified-fit":
                return None
            text_id = line.get("text_id")
            measurement = line.get("measurement")
            if not isinstance(text_id, str) or not text_id or not isinstance(measurement, dict):
                return None
            provenance = measurement.get("provenance")
            request = measurement.get("request")
            if (
                not isinstance(provenance, dict)
                or provenance.get("font_aware") is not True
                or not isinstance(request, dict)
            ):
                return None
            required = ("value", "font_postscript_name", "font_size", "tracking")
            if any(field not in request for field in required):
                return None
            if (
                not isinstance(request["value"], str)
                or not isinstance(request["font_postscript_name"], str)
                or isinstance(request["font_size"], bool)
                or not isinstance(request["font_size"], int | float)
                or isinstance(request["tracking"], bool)
                or not isinstance(request["tracking"], int | float)
            ):
                return None
            signatures.append(
                {
                    "id": text_id,
                    "text": request["value"],
                    "font_postscript_name": request["font_postscript_name"],
                    "font_size": request["font_size"],
                    "tracking": request["tracking"],
                }
            )
    if len({signature["id"] for signature in signatures}) != len(signatures):
        return None
    return sorted(signatures, key=lambda signature: signature["id"])


def _numbers_close(actual: Any, expected: float, *, tolerance: float = 1e-9) -> bool:
    return isinstance(actual, int | float) and abs(float(actual) - expected) <= tolerance


def _artboard_variant_correspondence(
    evidence: dict[str, Any], contract: ProductionContract
) -> bool:
    if not contract.artboard_variants:
        return True
    if len(contract.artboard_variants) != len(contract.artboards):
        return False
    artboards = {artboard.id: artboard for artboard in contract.artboards}
    group_names_by_id = evidence["group_names_by_id"]
    return all(
        (artboard := artboards.get(variant.artboard_id)) is not None
        and variant.component_id.endswith(f".{variant.semantic_key}")
        and variant.artboard_id == f"{variant.component_id}.artboard"
        and artboard.group_id == f"{variant.component_id}.group"
        and group_names_by_id.get(artboard.group_id) == artboard.name
        and all(
            item_id.startswith(f"{variant.component_id}.")
            for item_id in artboard.required_ids
        )
        for variant in contract.artboard_variants
    )


def _contract_checks(
    evidence: dict[str, Any],
    contract: ProductionContract,
    text_layout_report: Mapping[str, Any] | None,
) -> dict[str, bool]:
    ids = set(evidence["ids"])
    group_names = set(evidence["group_names"])
    layout_signatures = _verified_layout_signatures(text_layout_report)
    layout_verified = layout_signatures == evidence["point_text_signatures"]
    expected_artboards = [
        {
            "id": artboard.id,
            "name": artboard.name,
            "left": artboard.left,
            "top": artboard.top,
            "width": artboard.width,
            "height": artboard.height,
        }
        for artboard in contract.artboards
    ]
    expected_images = [
        {
            "id": image.id,
            "source": image.source,
            "x": image.x,
            "y": image.y,
            "width": image.width,
            "height": image.height,
        }
        for image in contract.linked_images
    ]
    expected_area_texts = [
        {
            "id": text.id,
            "width": text.width,
            "height": text.height,
            "leading": text.leading,
            "font_name": text.font_name,
        }
        for text in contract.area_texts
    ]
    artboard_content = all(
        set(artboard.required_ids)
        <= set(evidence["group_descendant_ids"].get(artboard.group_id, ()))
        for artboard in contract.artboards
    )
    area_texts_match = len(evidence["area_texts"]) == len(expected_area_texts) and all(
        actual["id"] == expected["id"]
        and actual["font_name"] == expected["font_name"]
        and all(
            _numbers_close(actual[key], expected[key])
            for key in ("width", "height", "leading")
        )
        for actual, expected in zip(
            evidence["area_texts"], expected_area_texts, strict=True
        )
    )
    return {
        "canvas_dimensions": (evidence["width"], evidence["height"])
        == (contract.width, contract.height),
        "layer_names": evidence["layer_names"] == list(contract.layer_names),
        "path_count": evidence["path_count"] == contract.path_count,
        "text_count": evidence["text_count"] == contract.text_count,
        "group_count": evidence["group_count"] == contract.group_count,
        "linked_images": evidence["linked_images"] == expected_images,
        "area_texts": area_texts_match,
        "artboards": evidence["artboards"] == expected_artboards,
        "artboard_content": artboard_content,
        "artboard_variant_correspondence": _artboard_variant_correspondence(
            evidence, contract
        ),
        "required_ids": set(contract.required_ids) <= ids,
        "required_group_names": set(contract.required_group_names) <= group_names,
        "required_fonts_declared": set(contract.required_fonts)
        <= set(evidence["font_postscript_names"]),
        "text_layout_verified": not contract.require_verified_text_layout
        or (
            layout_verified
            and text_layout_report is not None
            and set(contract.required_fonts)
            <= set(text_layout_report.get("font_postscript_names", ()))
        ),
    }


def evaluate_reference_document(
    build_document: DocumentFactory,
    contract: ProductionContract,
    text_layout_report: Mapping[str, Any] | None = None,
) -> tuple[Document, dict[str, Any]]:
    document = build_document()
    repeated = build_document()
    source_determinism = semantic_diff(document, repeated)
    encoded = json.dumps(document.to_dict(), ensure_ascii=False, sort_keys=True)
    reconstructed = Document.from_dict(json.loads(encoded))
    ir_roundtrip = semantic_diff(document, reconstructed)
    evidence = _document_evidence(document)
    checks = {
        "source_is_deterministic": source_determinism.equal,
        "ir_json_roundtrip": ir_roundtrip.equal,
        **_contract_checks(evidence, contract, text_layout_report),
    }
    return document, {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "document_evidence": evidence,
        "source_determinism": source_determinism.to_dict(),
        "ir_json_roundtrip": ir_roundtrip.to_dict(),
        "text_layout": dict(text_layout_report) if text_layout_report is not None else None,
    }


def verify_reference_document(
    build_document: DocumentFactory,
    *,
    contract: ProductionContract,
    text_layout_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the pure Document, determinism, IR roundtrip, and contract gate."""

    _, evidence = evaluate_reference_document(build_document, contract, text_layout_report)
    return evidence
