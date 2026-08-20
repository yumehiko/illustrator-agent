import os

import pytest

from examples.japanese_schedule.cli import PRODUCTION_CONTRACT
from examples.japanese_schedule.document import DOCUMENT_SOURCE, build_document, build_layout_report
from examples.japanese_schedule.input import DEFAULT_INPUT, load_schedule_input
from illustrator_agent.production import compile_reference_production

pytestmark = [
    pytest.mark.illustrator,
    pytest.mark.skipif(
        os.environ.get("RUN_ILLUSTRATOR_TESTS") != "1",
        reason="set RUN_ILLUSTRATOR_TESTS=1 for the Illustrator runtime gate",
    ),
]


def test_japanese_native_compile_font_preview_and_reopen(tmp_path) -> None:
    schedule = load_schedule_input()
    report = compile_reference_production(
        lambda: build_document(schedule),
        source=DOCUMENT_SOURCE,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=PRODUCTION_CONTRACT,
        text_layout_report=build_layout_report(schedule),
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["illustrator"]["fonts"]["status"] == "passed"
    assert report["illustrator"]["status"] == "passed"
    assert all(report["illustrator"]["checks"].values())
