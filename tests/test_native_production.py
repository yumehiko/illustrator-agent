from pathlib import Path
from types import SimpleNamespace

import pytest

from examples.japanese_schedule.cli import PRODUCTION_CONTRACT as JAPANESE_CONTRACT
from examples.japanese_schedule.document import (
    DOCUMENT_SOURCE as JAPANESE_SOURCE,
)
from examples.japanese_schedule.document import (
    build_document as build_japanese_document,
)
from examples.japanese_schedule.document import (
    build_layout_report,
)
from examples.japanese_schedule.input import (
    DEFAULT_INPUT as JAPANESE_INPUT,
)
from examples.japanese_schedule.input import (
    load_schedule_input,
)
from examples.quarterly_kpi_report.cli import PRODUCTION_CONTRACT
from examples.quarterly_kpi_report.document import DOCUMENT_SOURCE, build_document
from examples.quarterly_kpi_report.input import DEFAULT_INPUT, load_report_input
from illustrator_agent import production


def _fake_native_compile(document: object, destination: str | Path, **_: object) -> dict:
    Path(destination).write_bytes(b"native-ai")
    return {
        "status": "passed",
        "illustrator": {"ok": True, "checks": {"reopen": True}},
    }


def _fake_preview(source: str | Path, output: str | Path, **_: object) -> SimpleNamespace:
    Path(output).write_bytes(b"preview")
    return SimpleNamespace(to_dict=lambda: {"source": str(source), "page_count": 1})


def _fake_font_catalog(**_: object) -> dict:
    return {
        "status": "passed",
        "illustrator_version": "test",
        "missing": [],
    }


def test_production_uses_direct_native_compile_and_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(production, "compile_native_ai", _fake_native_compile)
    monkeypatch.setattr(production, "render_preview", _fake_preview)
    report_input = load_report_input()

    report = production.compile_reference_production(
        lambda: build_document(report_input),
        source=DOCUMENT_SOURCE,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=PRODUCTION_CONTRACT,
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["pure"]["status"] == "passed"
    assert all(report["illustrator"]["checks"].values())
    assert set(report["artifacts"]) == {"ir", "native_ai", "native_preview"}
    assert (tmp_path / "quarterly-kpi-report.native.ai").is_file()
    assert (tmp_path / "quarterly-kpi-report.native.preview.png").is_file()


def test_production_refuses_to_overwrite_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(production, "compile_native_ai", _fake_native_compile)
    monkeypatch.setattr(production, "render_preview", _fake_preview)
    report_input = load_report_input()
    arguments = {
        "source": DOCUMENT_SOURCE,
        "input_data": DEFAULT_INPUT,
        "output_directory": tmp_path,
        "contract": PRODUCTION_CONTRACT,
    }
    production.compile_reference_production(lambda: build_document(report_input), **arguments)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        production.compile_reference_production(lambda: build_document(report_input), **arguments)


def test_japanese_production_requires_font_catalog_and_verified_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(production, "compile_native_ai", _fake_native_compile)
    monkeypatch.setattr(production, "render_preview", _fake_preview)
    monkeypatch.setattr(production, "list_illustrator_fonts", _fake_font_catalog)
    schedule = load_schedule_input()

    report = production.compile_reference_production(
        lambda: build_japanese_document(schedule),
        source=JAPANESE_SOURCE,
        input_data=JAPANESE_INPUT,
        output_directory=tmp_path,
        contract=JAPANESE_CONTRACT,
        text_layout_report=build_layout_report(schedule),
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["pure"]["checks"]["text_layout_verified"] is True
    assert report["illustrator"]["checks"]["requested_fonts_available"] is True
    assert report["illustrator"]["fonts"] == {
        "status": "passed",
        "illustrator_version": "test",
        "required": ["KozGoPr6N-Regular"],
        "missing": [],
        "error": None,
    }


def test_font_catalog_environment_error_is_preserved_in_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        production,
        "list_illustrator_fonts",
        lambda **_: {
            "status": "environment-unavailable",
            "error": "Illustrator did not answer within 30 seconds.",
            "missing": None,
        },
    )
    schedule = load_schedule_input()

    report = production.compile_reference_production(
        lambda: build_japanese_document(schedule),
        source=JAPANESE_SOURCE,
        input_data=JAPANESE_INPUT,
        output_directory=tmp_path,
        contract=JAPANESE_CONTRACT,
        text_layout_report=build_layout_report(schedule),
    )

    assert report["status"] == "failed"
    assert report["illustrator"]["compile"]["status"] == "not-run"
    assert report["illustrator"]["fonts"]["error"] == (
        "Illustrator did not answer within 30 seconds."
    )
