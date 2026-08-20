"""Thin composition of data-driven campaign variants and artboards."""

from __future__ import annotations

from pathlib import Path

from illustrator_agent import Artboard, Document, LayerBuilder

from .components import CampaignVariant
from .identities import plan_campaign_identities
from .input import CampaignInput, load_campaign_input

DOCUMENT_SOURCE = Path(__file__)


def build_document(campaign: CampaignInput | None = None) -> Document:
    campaign = campaign or load_campaign_input()
    identities = plan_campaign_identities(campaign.variants)

    page = LayerBuilder(id=identities.layer, name="Campaign variants")
    artboards = []
    identity_map = {}
    for spec, ids in zip(campaign.variants, identities.variants, strict=True):
        component = CampaignVariant(campaign, spec, ids).render()
        page.add_grouped(component, group_id=ids.group, group_name=spec.name)
        artboards.append(
            Artboard(
                id=ids.artboard,
                name=spec.name,
                left=spec.left,
                top=spec.top,
                width=spec.width,
                height=spec.height,
            )
        )
        identity_map[spec.key] = {
            "component": ids.component,
            "artboard": ids.artboard,
            "group": ids.group,
        }

    return Document(
        width=campaign.width,
        height=campaign.height,
        title="Campaign variants with multiple artboards",
        metadata={
            "source": "examples/campaign_variants/document.py",
            "business_case": "multi-format-campaign",
            "identity_namespace": "campaign",
            "variant_identities": identity_map,
        },
        artboards=artboards,
        layers=[page.build()],
    )
