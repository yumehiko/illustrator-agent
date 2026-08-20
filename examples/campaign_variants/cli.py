"""CLI and production contract for data-driven campaign variants."""

from __future__ import annotations

from pathlib import Path

from examples.production_runner import ProductionRun, run_production_cli
from illustrator_agent.production import (
    ArtboardVariantContract,
    ProductionAreaText,
    ProductionArtboard,
    ProductionContract,
)

from .components import description_geometry
from .document import DOCUMENT_SOURCE, build_document
from .identities import plan_campaign_identities
from .input import DEFAULT_INPUT, CampaignInput, load_campaign_input

DEFAULT_OUTPUT = Path(__file__).parents[2] / "build" / "campaign-variants"


def production_contract(campaign: CampaignInput) -> ProductionContract:
    identities = plan_campaign_identities(campaign.variants)
    pairs = tuple(zip(campaign.variants, identities.variants, strict=True))
    artboards = tuple(
        ProductionArtboard(
            id=ids.artboard,
            name=spec.name,
            left=spec.left,
            top=spec.top,
            width=spec.width,
            height=spec.height,
            group_id=ids.group,
            required_ids=(
                ids.background,
                ids.accent,
                ids.title_line_0,
                ids.action_background,
            ),
        )
        for spec, ids in pairs
    )
    variants = tuple(
        ArtboardVariantContract(
            semantic_key=spec.key,
            component_id=ids.component,
            artboard_id=ids.artboard,
        )
        for spec, ids in pairs
    )
    area_texts = tuple(
        ProductionAreaText(
            id=ids.description,
            width=width,
            height=height,
            leading=11 * 1.35,
            font_name="Helvetica",
        )
        for spec, ids in pairs
        for width, height in (description_geometry(spec),)
    )
    return ProductionContract(
        production_id="campaign-variants",
        width=campaign.width,
        height=campaign.height,
        layer_names=("Campaign variants",),
        path_count=3 * len(artboards),
        text_count=6 * len(artboards),
        group_count=len(artboards),
        required_ids=(
            identities.layer,
            *(artboard.id for artboard in artboards),
            *(artboard.group_id for artboard in artboards),
        ),
        required_group_names=tuple(artboard.name for artboard in artboards),
        visual_acceptance=(
            "square、portrait、bannerの3 artboardが独立した完成レイアウトとして読める",
            "各artboardの背景、accent、見出し、説明、action、format labelが見切れない",
            "各variantが1 groupで選択でき、textとpathを個別編集できる",
        ),
        artboards=artboards,
        artboard_variants=variants,
        area_texts=area_texts,
    )


PRODUCTION_CONTRACT = production_contract(load_campaign_input())


def main(argv: list[str] | None = None) -> int:
    def prepare(input_path: Path | None) -> ProductionRun:
        assert input_path is not None
        campaign = load_campaign_input(input_path)
        return ProductionRun(
            build_document=lambda: build_document(campaign),
            source=DOCUMENT_SOURCE,
            input_data=input_path,
            contract=production_contract(campaign),
        )

    return run_production_cli(
        description=__doc__,
        default_input=DEFAULT_INPUT,
        default_output=DEFAULT_OUTPUT,
        prepare=prepare,
        argv=argv,
    )
