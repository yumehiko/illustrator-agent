import json
from pathlib import Path

import pytest

from examples.quarterly_kpi_report.cli import PRODUCTION_CONTRACT
from examples.quarterly_kpi_report.document import build_document
from examples.quarterly_kpi_report.input import DEFAULT_INPUT, load_report_input
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

    with pytest.raises(ValueError, match="metric.positive"):
        load_report_input(invalid)


def test_pure_gate_validates_determinism_ir_and_contract() -> None:
    report_input = load_report_input()
    evidence = verify_reference_document(
        lambda: build_document(report_input), contract=PRODUCTION_CONTRACT
    )

    assert evidence["status"] == "passed"
    assert all(evidence["checks"].values())
    assert evidence["document_evidence"]["path_count"] == 17
    assert evidence["document_evidence"]["text_count"] == 24
