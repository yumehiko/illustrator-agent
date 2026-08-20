"""Stable identity planning performed before campaign IR generation."""

from __future__ import annotations

from dataclasses import dataclass

from illustrator_agent import ComponentIdentity, IdentityNamespace

from .input import VariantSpec


@dataclass(frozen=True, slots=True)
class VariantIdentities:
    semantic_key: str
    component: str
    artboard: str
    group: str
    background: str
    accent: str
    eyebrow: str
    title: str
    description: str
    action_background: str
    action: str
    footer: str
    title_line_0: str


@dataclass(frozen=True, slots=True)
class CampaignIdentities:
    layer: str
    variants: tuple[VariantIdentities, ...]


def _claim_text_lines(component: ComponentIdentity, base: str, count: int) -> None:
    for index in range(count):
        component.claim(base, f"line-{index}")


def plan_campaign_identities(variants: tuple[VariantSpec, ...]) -> CampaignIdentities:
    """Validate every semantic key and final id before creating low-level IR."""

    namespace = IdentityNamespace("campaign")
    layer = namespace.claim("layer")
    plans = []
    for spec in variants:
        component = namespace.component(spec.key)
        artboard = component.claim("artboard")
        group = component.claim("group")
        background = component.claim("background")
        accent = component.claim("accent")
        eyebrow = component.claim("eyebrow")
        title = component.claim("title")
        description = component.claim("description")
        action_background = component.claim("action-background")
        action = component.claim("action")
        footer = component.claim("footer")
        _claim_text_lines(component, "eyebrow", 1)
        _claim_text_lines(component, "title", 2)
        _claim_text_lines(component, "action", 1)
        _claim_text_lines(component, "footer", 1)
        plans.append(
            VariantIdentities(
                semantic_key=spec.key,
                component=component.id,
                artboard=artboard,
                group=group,
                background=background,
                accent=accent,
                eyebrow=eyebrow,
                title=title,
                description=description,
                action_background=action_background,
                action=action,
                footer=footer,
                title_line_0=f"{title}.line-0",
            )
        )
    return CampaignIdentities(layer=layer, variants=tuple(plans))
