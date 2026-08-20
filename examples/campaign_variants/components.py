"""Editable component for one campaign format."""

from __future__ import annotations

from dataclasses import dataclass

from illustrator_agent import (
    AreaTextBlock,
    Color,
    FontSpec,
    LayerBuilder,
    RenderedComponent,
    TextBlock,
    TextStyle,
    ellipse_path,
    rectangle_path,
)

from .identities import VariantIdentities
from .input import CampaignInput, VariantSpec


def description_geometry(spec: VariantSpec) -> tuple[float, float]:
    """Return the editable description frame dimensions for a layout policy."""

    if spec.layout == "banner":
        return 270, 34
    return spec.width - 54, 52


@dataclass(frozen=True, slots=True)
class CampaignVariant:
    campaign: CampaignInput
    spec: VariantSpec
    identities: VariantIdentities

    def render(self) -> RenderedComponent:
        navy = Color(0.04, 0.08, 0.15)
        white = Color(1, 1, 1)
        lime = Color(0.72, 0.92, 0.24)
        coral = Color(0.96, 0.3, 0.2)
        muted = Color(0.73, 0.78, 0.84)
        spec = self.spec
        ids = self.identities
        title_width, description_height = description_geometry(spec)
        builder = LayerBuilder(id=ids.component, name=spec.name)
        builder.add_path(
            rectangle_path(
                ids.background,
                x=spec.left,
                top=spec.top,
                width=spec.width,
                height=spec.height,
                fill=navy,
                name="Background",
            )
        )

        if spec.layout == "banner":
            accent_x = spec.left + spec.width - 72
            accent_y = spec.top - spec.height / 2
            title_size = 27
            eyebrow_top = spec.top - 24
            title_top = spec.top - 59
            description_top = spec.top - 124
            action_x = spec.left + 320
            action_top = spec.top - 67
            action_width = 138
            footer_top = spec.top - 158
        else:
            accent_x = spec.left + spec.width - 58
            accent_y = spec.top - 60
            title_size = 32 if spec.layout == "square" else 27
            eyebrow_top = spec.top - 27
            title_top = spec.top - 86
            description_top = spec.top - 188
            action_x = spec.left + 27
            action_top = spec.top - 270
            action_width = min(164, spec.width - 54)
            footer_top = spec.top - spec.height + 24

        builder.add_path(
            ellipse_path(
                ids.accent,
                center_x=accent_x,
                center_y=accent_y,
                radius_x=62 if spec.layout == "banner" else 54,
                radius_y=62 if spec.layout == "banner" else 54,
                fill=coral,
                name="Campaign accent",
            )
        )
        builder.add(
            TextBlock(
                id=ids.eyebrow,
                name="Campaign series",
                text=self.campaign.eyebrow,
                width=spec.width - 54,
                wrap=False,
                style=TextStyle(
                    font_size=9,
                    font=FontSpec("Helvetica-Bold"),
                    tracking=160,
                    fill=lime,
                ),
            ).render(x=spec.left + 27, top=eyebrow_top)
        )
        builder.add(
            TextBlock(
                id=ids.title,
                name="Campaign title",
                text=self.campaign.title,
                width=title_width,
                wrap=False,
                style=TextStyle(
                    font_size=title_size,
                    font=FontSpec("Helvetica-Bold"),
                    line_height_ratio=0.98,
                    fill=white,
                ),
            ).render(x=spec.left + 27, top=title_top)
        )
        builder.add(
            AreaTextBlock(
                id=ids.description,
                name="Campaign description",
                text=self.campaign.description,
                width=title_width,
                height=description_height,
                style=TextStyle(
                    font_size=11,
                    font=FontSpec("Helvetica"),
                    line_height_ratio=1.35,
                    fill=muted,
                ),
            ).render(x=spec.left + 27, top=description_top)
        )
        builder.add_path(
            rectangle_path(
                ids.action_background,
                x=action_x,
                top=action_top,
                width=action_width,
                height=38,
                fill=lime,
                name="Action background",
            )
        )
        builder.add(
            TextBlock(
                id=ids.action,
                name="Action label",
                text=self.campaign.action,
                width=action_width,
                alignment="center",
                wrap=False,
                style=TextStyle(
                    font_size=11,
                    font=FontSpec("Helvetica-Bold"),
                    tracking=70,
                    fill=navy,
                ),
            ).render(x=action_x, top=action_top - 11)
        )
        builder.add(
            TextBlock(
                id=ids.footer,
                name="Format label",
                text=spec.name.upper(),
                width=spec.width - 54,
                alignment="right",
                wrap=False,
                style=TextStyle(
                    font_size=8,
                    font=FontSpec("Helvetica-Bold"),
                    tracking=120,
                    fill=muted,
                ),
            ).render(x=spec.left + 27, top=footer_top)
        )

        layer = builder.build()
        return RenderedComponent(
            width=spec.width,
            height=spec.height,
            paths=layer.paths,
            text_frames=layer.text_frames,
            item_order=layer.item_order,
        )
