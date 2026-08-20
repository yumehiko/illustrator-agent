"""CLI and production contract for data-driven campaign variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from illustrator_agent.production import (
    ArtboardVariantContract,
    ProductionAreaText,
    ProductionArtboard,
    ProductionContract,
    compile_reference_production,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--accept-visual-by")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    campaign = load_campaign_input(args.input)
    result = compile_reference_production(
        lambda: build_document(campaign),
        source=DOCUMENT_SOURCE,
        input_data=args.input,
        output_directory=args.output_dir,
        contract=production_contract(campaign),
        visual_accepted_by=args.accept_visual_by,
        force=args.force,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {"status": result["status"], "report": result["report_path"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["status"] in {"passed", "awaiting-visual-acceptance"} else 1
