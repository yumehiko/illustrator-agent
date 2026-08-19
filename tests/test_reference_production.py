import importlib.util
import json
import sys
from pathlib import Path

import pytest

from illustrator_agent.production import run_reference_production

EXAMPLE_PATH = Path(__file__).parents[1] / "examples" / "quarterly_kpi_report.py"
SPEC = importlib.util.spec_from_file_location("quarterly_kpi_report", EXAMPLE_PATH)
assert SPEC is not None and SPEC.loader is not None
EXAMPLE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EXAMPLE
SPEC.loader.exec_module(EXAMPLE)

DEFAULT_INPUT = EXAMPLE.DEFAULT_INPUT
M1_CONTRACT = EXAMPLE.M1_CONTRACT
build_document = EXAMPLE.build_document
load_report_input = EXAMPLE.load_report_input


def test_m1_input_builds_the_expected_semantic_document() -> None:
    report_input = load_report_input()

    document = build_document(report_input)

    assert (document.width, document.height) == (612, 420)
    assert [layer.name for layer in document.layers] == ["Quarterly KPI report"]
    assert document.metadata["business_case"] == "quarterly-kpi-report"
    assert report_input.metrics[2].positive is False


def test_m1_input_rejects_a_non_boolean_variant(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    raw["metrics"][0]["positive"] = "yes"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="metric.positive"):
        load_report_input(invalid)


def test_m1_static_pipeline_emits_passing_evidence(tmp_path: Path) -> None:
    report_input = load_report_input()

    report = run_reference_production(
        lambda: build_document(report_input),
        source=EXAMPLE_PATH,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=M1_CONTRACT,
    )

    assert report["status"] == "awaiting-illustrator"
    assert report["automated"]["status"] == "passed"
    assert all(report["automated"]["checks"].values())
    assert report["visual_acceptance"]["status"] == "pending"
    assert report["artifacts"]["legacy_ai"]["sha256"] == (
        "efc8df2192fd16d430ec7b1e70ec201b7e8b2f9a0968f50acd637c0725abe970"
    )
    assert (tmp_path / "quarterly-kpi-report.ai").is_file()
    assert (tmp_path / "quarterly-kpi-report.ir.json").is_file()
    assert (tmp_path / "quarterly-kpi-report.preview.png").is_file()
    assert (tmp_path / "report.json").is_file()


def test_m1_pipeline_refuses_to_overwrite_artifacts(tmp_path: Path) -> None:
    report_input = load_report_input()
    arguments = {
        "source": EXAMPLE_PATH,
        "input_data": DEFAULT_INPUT,
        "output_directory": tmp_path,
        "contract": M1_CONTRACT,
    }
    run_reference_production(lambda: build_document(report_input), **arguments)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_reference_production(lambda: build_document(report_input), **arguments)


def test_visual_acceptance_does_not_bypass_illustrator_gate(tmp_path: Path) -> None:
    report_input = load_report_input()

    report = run_reference_production(
        lambda: build_document(report_input),
        source=EXAMPLE_PATH,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=M1_CONTRACT,
        visual_accepted_by="user",
    )

    assert report["status"] == "awaiting-illustrator"
    assert report["visual_acceptance"] == {
        "status": "passed",
        "accepted_by": "user",
        "criteria": list(M1_CONTRACT.visual_acceptance),
    }
