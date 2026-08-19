import os
from pathlib import Path

import pytest

from examples.quarterly_kpi_report.cli import PRODUCTION_CONTRACT
from examples.quarterly_kpi_report.document import DOCUMENT_SOURCE, build_document
from examples.quarterly_kpi_report.input import DEFAULT_INPUT, load_report_input
from illustrator_agent.production import compile_reference_production

pytestmark = [
    pytest.mark.illustrator,
    pytest.mark.skipif(
        os.environ.get("RUN_ILLUSTRATOR_TESTS") != "1",
        reason="set RUN_ILLUSTRATOR_TESTS=1 for the Illustrator runtime gate",
    ),
]


def test_quarterly_kpi_native_compile_preview_and_reopen(tmp_path: Path) -> None:
    report_input = load_report_input()
    report = compile_reference_production(
        lambda: build_document(report_input),
        source=DOCUMENT_SOURCE,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=PRODUCTION_CONTRACT,
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["illustrator"]["status"] == "passed"
    assert all(report["illustrator"]["checks"].values())
