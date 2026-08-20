import os
from pathlib import Path

import pytest

from examples.campaign_variants.cli import PRODUCTION_CONTRACT
from examples.campaign_variants.document import DOCUMENT_SOURCE, build_document
from examples.campaign_variants.input import DEFAULT_INPUT, load_campaign_input
from illustrator_agent.production import compile_reference_production

pytestmark = [
    pytest.mark.illustrator,
    pytest.mark.skipif(
        os.environ.get("RUN_ILLUSTRATOR_TESTS") != "1",
        reason="set RUN_ILLUSTRATOR_TESTS=1 for the Illustrator runtime gate",
    ),
]


def test_campaign_variants_native_compile_preview_and_reopen(tmp_path: Path) -> None:
    campaign = load_campaign_input()
    report = compile_reference_production(
        lambda: build_document(campaign),
        source=DOCUMENT_SOURCE,
        input_data=DEFAULT_INPUT,
        output_directory=tmp_path,
        contract=PRODUCTION_CONTRACT,
    )

    assert report["status"] == "awaiting-visual-acceptance"
    assert report["illustrator"]["status"] == "passed"
    assert all(report["illustrator"]["checks"].values())
    assert report["pure"]["checks"]["artboard_variant_correspondence"]
