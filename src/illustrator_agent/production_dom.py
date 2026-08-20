"""Production contract checks for reopened Illustrator DOM snapshots."""

from __future__ import annotations

import json
from typing import Any

from .production_contract import ProductionContract


def _stable_id(value: dict[str, Any], *, kind: str) -> str | None:
    note = value.get("note")
    prefix = f"py-ai-{kind}:"
    if not isinstance(note, str) or not note.startswith(prefix):
        return None
    try:
        identity = json.loads(note[len(prefix) :])
    except json.JSONDecodeError:
        return None
    item_id = identity.get("id") if isinstance(identity, dict) else None
    return item_id if isinstance(item_id, str) else None


def _numbers_close(actual: Any, expected: float, *, tolerance: float = 0.25) -> bool:
    return isinstance(actual, int | float) and abs(float(actual) - expected) <= tolerance


def illustrator_contract_checks(
    inspection: dict[str, Any], contract: ProductionContract
) -> dict[str, bool]:
    """Compare a Layer 1 Illustrator DOM inspection with the production contract."""

    actual = inspection.get("illustrator", {})
    placed_images = {
        item_id: value
        for value in actual.get("placed_images", [])
        if (item_id := _stable_id(value, kind="image")) is not None
    }
    text_frames = {
        item_id: value
        for value in actual.get("text_frames", [])
        if (item_id := _stable_id(value, kind="text")) is not None
    }
    expected_artboards = [
        {
            "name": artboard.name,
            "rect": [
                artboard.left,
                artboard.top,
                artboard.left + artboard.width,
                artboard.top - artboard.height,
            ],
        }
        for artboard in contract.artboards
    ]
    artboards_match = len(actual.get("artboards", [])) == len(expected_artboards) and all(
        board.get("name") == expected["name"]
        and len(board.get("rect", [])) == 4
        and all(
            _numbers_close(value, coordinate)
            for value, coordinate in zip(board["rect"], expected["rect"], strict=True)
        )
        for board, expected in zip(actual.get("artboards", []), expected_artboards, strict=True)
    )
    if not contract.artboards:
        artboards_match = True
    image_placements_match = all(
        (placed := placed_images.get(expected.id)) is not None
        and len(placed.get("position", [])) == 2
        and _numbers_close(placed["position"][0], expected.x)
        and _numbers_close(placed["position"][1], expected.y)
        and _numbers_close(placed.get("width"), expected.width)
        and _numbers_close(placed.get("height"), expected.height)
        for expected in contract.linked_images
    ) and len(placed_images) == len(contract.linked_images)
    area_texts_editable = all(
        (frame := text_frames.get(expected.id)) is not None
        and "AREATEXT" in str(frame.get("kind", "")).upper()
        and _numbers_close(frame.get("width"), expected.width)
        and _numbers_close(frame.get("height"), expected.height)
        and _numbers_close(frame.get("leading"), expected.leading)
        and frame.get("font_name") == expected.font_name
        for expected in contract.area_texts
    )
    no_area_text_overflow = all(
        text_frames.get(expected.id, {}).get("overflows") is False
        for expected in contract.area_texts
    )
    return {
        "dom_reopen_inspection": inspection.get("status") == "passed",
        "linked_assets_exist": all(
            placed_images.get(expected.id, {}).get("file_exists") is True
            for expected in contract.linked_images
        ),
        "linked_image_placements": image_placements_match,
        "native_artboards": artboards_match,
        "editable_area_texts": area_texts_editable,
        "area_texts_do_not_overflow": no_area_text_overflow,
    }
