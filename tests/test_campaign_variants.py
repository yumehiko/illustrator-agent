import json
from dataclasses import replace
from pathlib import Path

import pytest

from examples.campaign_variants.cli import PRODUCTION_CONTRACT
from examples.campaign_variants.document import build_document
from examples.campaign_variants.input import (
    DEFAULT_INPUT,
    VariantSpec,
    load_campaign_input,
)
from illustrator_agent import Document, InputValidationError
from illustrator_agent.production import verify_reference_document


def _variant_identities(document: Document) -> dict[str, dict[str, str]]:
    return document.metadata["variant_identities"]


def test_three_variants_have_traceable_artboards_groups_and_items() -> None:
    campaign = load_campaign_input()
    document = build_document(campaign)

    assert [artboard.name for artboard in document.artboards] == [
        "Square 1x1",
        "Portrait 3x4",
        "Banner 3x1",
    ]
    assert [
        (artboard.left, artboard.top, artboard.width, artboard.height)
        for artboard in document.artboards
    ] == [
        (20, 380, 360, 360),
        (400, 380, 270, 360),
        (690, 380, 540, 180),
    ]
    identities = _variant_identities(document)
    assert identities["square"] == {
        "component": "campaign.square",
        "artboard": "campaign.square.artboard",
        "group": "campaign.square.group",
    }
    assert [group.id for group in document.layers[0].groups] == [
        identities[variant.key]["group"] for variant in campaign.variants
    ]


def test_variant_ids_survive_reorder_addition_and_removal() -> None:
    campaign = load_campaign_input()
    baseline = _variant_identities(build_document(campaign))
    reordered = replace(campaign, variants=tuple(reversed(campaign.variants)))
    extra = VariantSpec("story", "Story banner", 690, 180, 540, 160, "banner")
    added = replace(campaign, variants=(extra, *campaign.variants))
    removed = replace(campaign, variants=(campaign.variants[0], campaign.variants[2]))

    assert _variant_identities(build_document(reordered)) == baseline
    assert {
        key: value
        for key, value in _variant_identities(build_document(added)).items()
        if key != "story"
    } == baseline
    assert _variant_identities(build_document(removed)) == {
        key: baseline[key] for key in ("square", "banner")
    }


def test_campaign_input_rejects_duplicate_semantic_keys_before_document_build(
    tmp_path: Path,
) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["variants"][1]["key"] = raw["variants"][0]["key"]
    invalid = tmp_path / "duplicate.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InputValidationError) as caught:
        load_campaign_input(invalid)

    assert caught.value.path == "$.variants"


def test_campaign_input_rejects_invalid_semantic_key_before_document_build(
    tmp_path: Path,
) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["variants"][0]["key"] = "square.group"
    invalid = tmp_path / "invalid-key.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InputValidationError) as caught:
        load_campaign_input(invalid)

    assert caught.value.path == "$.variants[0]"


def test_campaign_pure_gate_checks_artboard_variant_contract() -> None:
    campaign = load_campaign_input()
    evidence = verify_reference_document(
        lambda: build_document(campaign), contract=PRODUCTION_CONTRACT
    )

    assert evidence["status"] == "passed"
    assert all(evidence["checks"].values())
    assert evidence["document_evidence"]["artboards"][2] == {
        "id": "campaign.banner.artboard",
        "name": "Banner 3x1",
        "left": 690.0,
        "top": 380.0,
        "width": 540.0,
        "height": 180.0,
    }


def test_campaign_contract_rejects_wrong_artboard_group_correspondence() -> None:
    campaign = load_campaign_input()
    first, second, third = PRODUCTION_CONTRACT.artboards
    mismatched = replace(first, group_id=second.group_id)
    contract = replace(
        PRODUCTION_CONTRACT,
        artboards=(mismatched, second, third),
    )

    evidence = verify_reference_document(lambda: build_document(campaign), contract=contract)

    assert evidence["status"] == "failed"
    assert evidence["checks"]["artboard_variant_correspondence"] is False
