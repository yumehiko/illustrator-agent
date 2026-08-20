import json
from collections.abc import Callable
from pathlib import Path

import pytest

from examples.japanese_schedule.cli import PRODUCTION_CONTRACT
from examples.japanese_schedule.document import build_document, build_layout_report
from examples.japanese_schedule.input import DEFAULT_INPUT, load_schedule_input
from illustrator_agent import (
    InputValidationError,
    MissingTextMeasurementError,
    TextOverflowError,
)
from illustrator_agent.production import verify_reference_document


def _changed_input(tmp_path: Path, change: Callable[[dict], None]) -> Path:
    raw = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    change(raw)
    destination = tmp_path / "schedule.json"
    destination.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    return destination


def test_explicit_input_builds_editable_stable_point_text() -> None:
    schedule = load_schedule_input()
    document = build_document(schedule)
    group = document.layers[0].groups[0]

    assert document.layers[0].id == "japanese-schedule"
    assert group.id == "event-schedule.group"
    assert len(group.text_frames) == 18
    assert all(text.area_width is None for text in group.text_frames)
    assert group.text_frames[9].text.endswith("デザイン制")
    assert group.text_frames[10].text == "作の考え方"
    assert "、" in schedule.rows[1].description


def test_input_rejects_a_blank_required_cell(tmp_path: Path) -> None:
    path = _changed_input(tmp_path, lambda raw: raw["rows"][0].update(description=""))

    with pytest.raises(InputValidationError) as caught:
        load_schedule_input(path)

    assert caught.value.path == "$.rows[0].description"


def test_input_rejects_overlong_text(tmp_path: Path) -> None:
    path = _changed_input(tmp_path, lambda raw: raw["rows"][0].update(description="長" * 81))

    with pytest.raises(InputValidationError, match="at most 80") as caught:
        load_schedule_input(path)

    assert caught.value.path == "$.rows[0].description"


def test_input_rejects_too_many_rows(tmp_path: Path) -> None:
    def add_rows(raw: dict) -> None:
        raw["rows"] = [raw["rows"][0]] * 9

    path = _changed_input(tmp_path, add_rows)

    with pytest.raises(InputValidationError) as caught:
        load_schedule_input(path)

    assert caught.value.path == "$.rows"


def test_approximation_provenance_cannot_pass_fail_closed_production(tmp_path: Path) -> None:
    path = _changed_input(
        tmp_path,
        lambda raw: raw["measurement_provenance"].update(
            method="unicode-width-heuristic-v1",
            font_aware=False,
            source="illustrator-agent",
        ),
    )
    schedule = load_schedule_input(path)

    with pytest.raises(TextOverflowError, match="rejected-unverified"):
        build_layout_report(schedule)


def test_missing_exact_measurement_fails_closed(tmp_path: Path) -> None:
    def remove_header_measurement(raw: dict) -> None:
        raw["measurements"] = [
            measurement
            for measurement in raw["measurements"]
            if measurement["text"] != "内容"
        ]

    schedule = load_schedule_input(_changed_input(tmp_path, remove_header_measurement))

    with pytest.raises(MissingTextMeasurementError):
        build_layout_report(schedule)


def test_pure_gate_includes_font_and_layout_provenance() -> None:
    schedule = load_schedule_input()
    layout = build_layout_report(schedule)
    evidence = verify_reference_document(
        lambda: build_document(schedule),
        contract=PRODUCTION_CONTRACT,
        text_layout_report=layout,
    )

    assert evidence["status"] == "passed"
    assert all(evidence["checks"].values())
    assert evidence["document_evidence"]["font_postscript_names"] == [
        "KozGoPr6N-Regular"
    ]
    assert evidence["document_evidence"]["point_text_count"] == 18
    assert evidence["text_layout"]["status"] == "verified-fit"
    provenance = evidence["text_layout"]["cells"][0]["lines"][0]["measurement"][
        "provenance"
    ]
    assert provenance["font_aware"] is True
    assert provenance["method"] == "adobe-illustrator-point-text-width"


def test_production_contract_inspects_each_measurements_provenance() -> None:
    schedule = load_schedule_input()
    layout = json.loads(json.dumps(build_layout_report(schedule), ensure_ascii=False))
    layout["cells"][0]["lines"][0]["measurement"]["provenance"]["font_aware"] = False

    evidence = verify_reference_document(
        lambda: build_document(schedule),
        contract=PRODUCTION_CONTRACT,
        text_layout_report=layout,
    )

    assert evidence["status"] == "failed"
    assert evidence["checks"]["text_layout_verified"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("value", "改変された時刻"),
        ("font_postscript_name", "Helvetica"),
        ("font_size", 99),
        ("tracking", 100),
    ),
)
def test_production_contract_rejects_layout_request_mismatch(
    field: str,
    replacement: str | int,
) -> None:
    schedule = load_schedule_input()
    layout = json.loads(json.dumps(build_layout_report(schedule), ensure_ascii=False))
    request = layout["cells"][0]["lines"][0]["measurement"]["request"]
    request[field] = replacement

    evidence = verify_reference_document(
        lambda: build_document(schedule),
        contract=PRODUCTION_CONTRACT,
        text_layout_report=layout,
    )

    assert evidence["status"] == "failed"
    assert evidence["checks"]["text_layout_verified"] is False


def test_production_contract_rejects_a_missing_layout_line() -> None:
    schedule = load_schedule_input()
    layout = json.loads(json.dumps(build_layout_report(schedule), ensure_ascii=False))
    layout["cells"][0]["lines"].clear()

    evidence = verify_reference_document(
        lambda: build_document(schedule),
        contract=PRODUCTION_CONTRACT,
        text_layout_report=layout,
    )

    assert evidence["document_evidence"]["point_text_count"] == 18
    assert evidence["checks"]["text_layout_verified"] is False
