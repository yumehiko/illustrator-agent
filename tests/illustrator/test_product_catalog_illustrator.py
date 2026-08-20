import os
from pathlib import Path

import pytest

from examples.product_catalog import (
    DOCUMENT_SOURCE,
    LINK,
    PRODUCTION_CONTRACT,
    build_document,
)
from illustrator_agent.production import compile_reference_production

pytestmark = [
    pytest.mark.illustrator,
    pytest.mark.skipif(
        os.environ.get("RUN_ILLUSTRATOR_TESTS") != "1",
        reason="set RUN_ILLUSTRATOR_TESTS=1 for the Illustrator runtime gate",
    ),
]


def test_product_catalog_link_area_text_artboards_and_preview(tmp_path: Path) -> None:
    report = compile_reference_production(
        build_document,
        source=DOCUMENT_SOURCE,
        input_data=LINK,
        output_directory=tmp_path,
        contract=PRODUCTION_CONTRACT,
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["illustrator"]["status"] == "passed"
    assert all(report["illustrator"]["checks"].values())
    inspection = report["illustrator"]["inspection"]["illustrator"]
    assert len(inspection["placed_images"]) == 2
    assert len(inspection["artboards"]) == 2
    assert all(
        frame["overflows"] is False
        for frame in inspection["text_frames"]
        if "AREATEXT" in frame["kind"].upper()
    )
