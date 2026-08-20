"""Document assembly for the product catalog production."""

from __future__ import annotations

from pathlib import Path

from py_ai_illustrator.model import Document

from illustrator_agent import LayerBuilder

from .components import (
    INTRINSIC_HEIGHT,
    INTRINSIC_WIDTH,
    LANDSCAPE,
    PORTRAIT,
    render_landscape_card,
    render_portrait_card,
)

EXAMPLES_ROOT = Path(__file__).parents[1]
DOCUMENT_SOURCE = Path(__file__)
LINK = EXAMPLES_ROOT / "Links" / "product-swatch.png"


def _require_source_asset() -> None:
    if not LINK.is_file():
        raise FileNotFoundError(f"required linked image fixture does not exist: {LINK}")


def build_document() -> Document:
    _require_source_asset()
    page = LayerBuilder(id="catalog", name="Product catalog")
    page.add_grouped(
        render_landscape_card(),
        group_id="catalog.landscape.group",
        group_name=LANDSCAPE.name,
    )
    page.add_grouped(
        render_portrait_card(),
        group_id="catalog.portrait.group",
        group_name=PORTRAIT.name,
    )
    return Document(
        width=1070,
        height=440,
        title="Linked image and area text product catalog",
        layers=[page.build()],
        artboards=[LANDSCAPE, PORTRAIT],
        metadata={
            "source": "examples/product_catalog/document.py",
            "business_case": "linked-image-area-text-multi-artboard-catalog",
            "asset_policy": "checked-in-deterministic-fixture-packaged-as-external-link",
            "asset_intrinsic_dimensions": [INTRINSIC_WIDTH, INTRINSIC_HEIGHT],
            "image_fit_policy": "contain",
        },
    )
