"""Pure production contract, determinism, and IR roundtrip verification."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from py_ai_illustrator.model import Document
from py_ai_illustrator.semantic import semantic_diff

from .production_contract import DocumentFactory, ProductionContract
from .production_evidence import document_evidence, verified_layout_signatures


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
    layout_signatures = verified_layout_signatures(text_layout_report)
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
    """Build a Document and return it with the complete pure-gate report."""

    document = build_document()
    repeated = build_document()
    source_determinism = semantic_diff(document, repeated)
    encoded = json.dumps(document.to_dict(), ensure_ascii=False, sort_keys=True)
    reconstructed = Document.from_dict(json.loads(encoded))
    ir_roundtrip = semantic_diff(document, reconstructed)
    evidence = document_evidence(document)
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
