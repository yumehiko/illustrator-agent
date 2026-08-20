import json
from pathlib import Path

import pytest
from py_ai_illustrator import iter_linked_images, package_linked_images

from examples.generate_product_swatch import product_swatch_png
from examples.product_catalog import (
    DOCUMENT_SOURCE,
    LINK,
    PRODUCTION_CONTRACT,
    build_document,
)
from examples.product_catalog import document as product_catalog_document
from illustrator_agent.production import verify_reference_document
from illustrator_agent.production_dom import illustrator_contract_checks


def test_product_catalog_passes_multi_artboard_production_contract() -> None:
    evidence = verify_reference_document(build_document, contract=PRODUCTION_CONTRACT)

    assert evidence["status"] == "passed"
    assert all(evidence["checks"].values())
    assert evidence["document_evidence"]["linked_image_count"] == 2
    assert len(evidence["document_evidence"]["area_texts"]) == 2
    assert len(evidence["document_evidence"]["artboards"]) == 2


def test_build_uses_the_checked_in_fixture_without_modifying_it() -> None:
    original = LINK.read_bytes()

    first = build_document()
    second = build_document()

    assert LINK.read_bytes() == original
    assert original == product_swatch_png()
    assert first.to_dict() == second.to_dict()


def test_build_fails_closed_when_the_source_asset_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing.png"
    monkeypatch.setattr(product_catalog_document, "LINK", missing)

    with pytest.raises(FileNotFoundError, match="required linked image fixture"):
        product_catalog_document.build_document()


def test_old_link_source_fails_from_the_package_document_base(tmp_path: Path) -> None:
    document = build_document()
    for image in iter_linked_images(document):
        image.source = "Links/product-swatch.png"

    with pytest.raises(ValueError, match=r"product_catalog/Links/product-swatch\.png"):
        package_linked_images(
            document,
            tmp_path / "invalid-package",
            source_base=DOCUMENT_SOURCE.parent,
        )


def test_layer_one_packaging_resolves_fixture_and_copies_then_reuses(
    tmp_path: Path,
) -> None:
    document = build_document()
    package = tmp_path / "package"

    first_document, first = package_linked_images(
        document,
        package,
        source_base=DOCUMENT_SOURCE.parent,
    )
    second_document, second = package_linked_images(
        document,
        package,
        source_base=DOCUMENT_SOURCE.parent,
    )

    assert [result.status for result in first] == ["copied", "reused"]
    assert [result.status for result in second] == ["reused", "reused"]
    assert all(result.source == LINK.resolve() for result in (*first, *second))
    assert all(result.destination == package / "Links" / LINK.name for result in first)
    assert (package / "Links" / LINK.name).read_bytes() == LINK.read_bytes()
    assert [image.source for image in iter_linked_images(first_document)] == [
        "Links/product-swatch.png",
        "Links/product-swatch.png",
    ]
    assert [image.source for image in iter_linked_images(second_document)] == [
        "Links/product-swatch.png",
        "Links/product-swatch.png",
    ]


def test_each_artboard_group_keeps_its_major_editable_items() -> None:
    document = build_document()
    groups = {group.id: group for group in document.layers[0].groups}

    for artboard in PRODUCTION_CONTRACT.artboards:
        group = groups[artboard.group_id]
        item_ids = {
            *(path.id for path in group.paths),
            *(text.id for text in group.text_frames),
            *(image.id for image in group.linked_images),
        }
        assert set(artboard.required_ids) <= item_ids
        assert len(group.linked_images) == 1
        assert sum(text.is_area_text for text in group.text_frames) == 1


def _identity_note(kind: str, item_id: str) -> str:
    return f"py-ai-{kind}:" + json.dumps(
        {"id": item_id, "name": None}, separators=(",", ":")
    )


def _passing_dom_inspection() -> dict:
    return {
        "status": "passed",
        "illustrator": {
            "placed_images": [
                {
                    "note": _identity_note("image", image.id),
                    "file_exists": True,
                    "position": [image.x, image.y],
                    "width": image.width,
                    "height": image.height,
                }
                for image in PRODUCTION_CONTRACT.linked_images
            ],
            "text_frames": [
                {
                    "note": _identity_note("text", text.id),
                    "kind": "TextType.AREATEXT",
                    "width": text.width,
                    "height": text.height,
                    "leading": text.leading,
                    "font_name": text.font_name,
                    "overflows": False,
                }
                for text in PRODUCTION_CONTRACT.area_texts
            ],
            "artboards": [
                {
                    "name": artboard.name,
                    "rect": [
                        artboard.left,
                        artboard.top,
                        artboard.left + artboard.width,
                        artboard.top - artboard.height,
                    ],
                }
                for artboard in PRODUCTION_CONTRACT.artboards
            ],
        },
    }


def test_dom_contract_accepts_links_placements_area_text_and_artboards() -> None:
    checks = illustrator_contract_checks(_passing_dom_inspection(), PRODUCTION_CONTRACT)

    assert all(checks.values())


def test_dom_contract_fails_closed_on_area_text_overset() -> None:
    inspection = _passing_dom_inspection()
    inspection["illustrator"]["text_frames"][0]["overflows"] = True

    checks = illustrator_contract_checks(inspection, PRODUCTION_CONTRACT)

    assert checks["area_texts_do_not_overflow"] is False
