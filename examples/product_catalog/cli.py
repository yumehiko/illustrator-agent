"""CLI and production contract for the linked-image product catalog."""

from __future__ import annotations

from pathlib import Path

from py_ai_illustrator.model import LinkedImage

from examples.production_runner import ProductionRun, run_production_cli
from illustrator_agent.production import (
    ProductionAreaText,
    ProductionArtboard,
    ProductionContract,
    ProductionLinkedImage,
)

from .components import LANDSCAPE, PORTRAIT, landscape_image, portrait_image
from .document import DOCUMENT_SOURCE, LINK, build_document

DEFAULT_OUTPUT = Path(__file__).parents[2] / "build" / "product-catalog"


def _image_contract(image: LinkedImage) -> ProductionLinkedImage:
    return ProductionLinkedImage(
        id=image.id,
        source=image.source,
        x=image.x,
        y=image.y,
        width=image.width,
        height=image.height,
    )


PRODUCTION_CONTRACT = ProductionContract(
    production_id="product-catalog",
    width=1070,
    height=440,
    layer_names=("Product catalog",),
    path_count=5,
    text_count=9,
    group_count=2,
    required_ids=(
        "catalog",
        "catalog.landscape.group",
        "catalog.landscape.photo",
        "catalog.landscape.description",
        "catalog.portrait.group",
        "catalog.portrait.photo",
        "catalog.portrait.description",
    ),
    required_group_names=(LANDSCAPE.name, PORTRAIT.name),
    artboards=(
        ProductionArtboard(
            id=LANDSCAPE.id,
            name=LANDSCAPE.name,
            left=LANDSCAPE.left,
            top=LANDSCAPE.top,
            width=LANDSCAPE.width,
            height=LANDSCAPE.height,
            group_id="catalog.landscape.group",
            required_ids=(
                "catalog.landscape.background",
                "catalog.landscape.photo",
                "catalog.landscape.description",
            ),
        ),
        ProductionArtboard(
            id=PORTRAIT.id,
            name=PORTRAIT.name,
            left=PORTRAIT.left,
            top=PORTRAIT.top,
            width=PORTRAIT.width,
            height=PORTRAIT.height,
            group_id="catalog.portrait.group",
            required_ids=(
                "catalog.portrait.background",
                "catalog.portrait.photo",
                "catalog.portrait.description",
            ),
        ),
    ),
    linked_images=(
        _image_contract(landscape_image()),
        _image_contract(portrait_image()),
    ),
    area_texts=(
        ProductionAreaText(
            id="catalog.landscape.description",
            width=296,
            height=96,
            leading=15.4,
            font_name="Helvetica",
        ),
        ProductionAreaText(
            id="catalog.portrait.description",
            width=262,
            height=54,
            leading=13.5,
            font_name="Helvetica",
        ),
    ),
    visual_acceptance=(
        "両artboardで画像全体が縦横比を保って表示され、stretchやcropがない",
        "両artboardのarea textが見切れず読みやすく、主要要素の余白と階層が意図どおりである",
        "linked image、area text、artboard別groupがIllustratorで個別に編集できる",
    ),
)


def main(argv: list[str] | None = None) -> int:
    def prepare(input_path: Path | None) -> ProductionRun:
        assert input_path is None
        return ProductionRun(
            build_document=build_document,
            source=DOCUMENT_SOURCE,
            input_data=LINK,
            contract=PRODUCTION_CONTRACT,
        )

    return run_production_cli(
        description=__doc__,
        default_output=DEFAULT_OUTPUT,
        prepare=prepare,
        argv=argv,
    )
