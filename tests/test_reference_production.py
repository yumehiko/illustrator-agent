import json
from pathlib import Path

import pytest

from examples.quarterly_kpi_report.cli import PRODUCTION_CONTRACT
from examples.quarterly_kpi_report.document import build_document
from examples.quarterly_kpi_report.input import DEFAULT_INPUT, load_report_input
from illustrator_agent import InputValidationError
from illustrator_agent.production import verify_reference_document


def test_input_builds_the_expected_semantic_document() -> None:
    report_input = load_report_input()
    document = build_document(report_input)

    assert (document.width, document.height) == (612, 420)
    assert [layer.name for layer in document.layers] == ["Quarterly KPI report"]
    assert document.metadata["business_case"] == "quarterly-kpi-report"
    assert report_input.metrics[2].positive is False


def test_input_rejects_a_non_boolean_variant(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["metrics"][0]["positive"] = "yes"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InputValidationError) as caught:
        load_report_input(invalid)

    assert caught.value.path == "$.metrics[0].positive"


def test_input_rejects_a_cross_field_chart_mismatch(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["chart"]["values"].pop()
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InputValidationError) as caught:
        load_report_input(invalid)

    assert caught.value.path == "$.chart"


def test_input_rejects_the_wrong_metric_count(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["metrics"].pop()
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InputValidationError) as caught:
        load_report_input(invalid)

    assert caught.value.path == "$.metrics"


def test_pure_gate_validates_determinism_ir_and_contract() -> None:
    report_input = load_report_input()
    evidence = verify_reference_document(
        lambda: build_document(report_input), contract=PRODUCTION_CONTRACT
    )

    assert evidence["status"] == "passed"
    assert all(evidence["checks"].values())
    assert evidence["document_evidence"]["path_count"] == 17
    assert evidence["document_evidence"]["text_count"] == 24


def test_pure_gate_report_schema_remains_stable() -> None:
    report_input = load_report_input()
    evidence = verify_reference_document(
        lambda: build_document(report_input), contract=PRODUCTION_CONTRACT
    )

    assert set(evidence) == {
        "status",
        "checks",
        "document_evidence",
        "source_determinism",
        "ir_json_roundtrip",
        "text_layout",
    }
    assert set(evidence["checks"]) == {
        "source_is_deterministic",
        "ir_json_roundtrip",
        "canvas_dimensions",
        "layer_names",
        "path_count",
        "text_count",
        "group_count",
        "linked_images",
        "area_texts",
        "artboards",
        "artboard_content",
        "artboard_variant_correspondence",
        "required_ids",
        "required_group_names",
        "required_fonts_declared",
        "text_layout_verified",
    }


def test_pure_gate_fails_on_nondeterministic_document_build() -> None:
    report_input = load_report_input()
    calls = 0

    def build_nondeterministically():
        nonlocal calls
        document = build_document(report_input)
        calls += 1
        document.width += calls - 1
        return document

    evidence = verify_reference_document(
        build_nondeterministically, contract=PRODUCTION_CONTRACT
    )

    assert evidence["status"] == "failed"
    assert evidence["checks"]["source_is_deterministic"] is False
    assert evidence["checks"]["ir_json_roundtrip"] is True
