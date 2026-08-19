from pathlib import Path
from types import SimpleNamespace

import pytest

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
