"""Artboard-specific components for the product catalog production."""

from __future__ import annotations

from py_ai_illustrator.model import Color, LinkedImage

from illustrator_agent import (
    AreaTextBlock,
    Artboard,
    FontSpec,
    LayerBuilder,
    RenderedComponent,
    TextBlock,
    TextStyle,
    ellipse_path,
    fit_linked_image,
    rectangle_path,
)

LINK_SOURCE = "../Links/product-swatch.png"
INTRINSIC_WIDTH = 320.0
INTRINSIC_HEIGHT = 220.0

LANDSCAPE = Artboard(
    id="catalog.landscape",
    name="Landscape catalog card",
    left=20,
    top=420,
    width=700,
    height=400,
)
PORTRAIT = Artboard(
    id="catalog.portrait",
    name="Portrait catalog card",
    left=740,
    top=420,
    width=310,
    height=400,
)


def landscape_image() -> LinkedImage:
    return fit_linked_image(
        id="catalog.landscape.photo",
        name="Landscape linked product image",
        source=LINK_SOURCE,
        intrinsic_width=INTRINSIC_WIDTH,
        intrinsic_height=INTRINSIC_HEIGHT,
        target_x=44,
        target_top=376,
        target_width=300,
        target_height=250,
        fit_policy="contain",
        horizontal_alignment="center",
        vertical_alignment="center",
    )


def portrait_image() -> LinkedImage:
    return fit_linked_image(
        id="catalog.portrait.photo",
        name="Portrait linked product image",
        source=LINK_SOURCE,
        intrinsic_width=INTRINSIC_WIDTH,
        intrinsic_height=INTRINSIC_HEIGHT,
        target_x=764,
        target_top=376,
        target_width=262,
        target_height=150,
        fit_policy="contain",
        horizontal_alignment="center",
        vertical_alignment="center",
    )


def render_landscape_card() -> RenderedComponent:
    builder = LayerBuilder(id="catalog.landscape.content", name=LANDSCAPE.name)
    builder.add_path(
        rectangle_path(
            "catalog.landscape.background",
            name="Landscape card background",
            x=LANDSCAPE.left,
            top=LANDSCAPE.top,
            width=LANDSCAPE.width,
            height=LANDSCAPE.height,
            fill=Color(0.96, 0.97, 0.99),
        )
    )
    builder.add_image(landscape_image())
    builder.add_path(
        ellipse_path(
            "catalog.landscape.badge",
            name="New badge",
            center_x=318,
            center_y=350,
            radius_x=30,
            radius_y=30,
            fill=Color(0.98, 0.37, 0.22),
        )
    )
    builder.add(
        TextBlock(
            id="catalog.landscape.badge-label",
            name="Badge label",
            text="NEW",
            width=52,
            alignment="center",
            wrap=False,
            style=TextStyle(
                font_size=11,
                font=FontSpec("Helvetica-Bold"),
                fill=Color(1, 1, 1),
            ),
        ).render(x=292, top=356)
    )
    builder.add(
        TextBlock(
            id="catalog.landscape.eyebrow",
            name="Category",
            text="STUDIO ESSENTIALS",
            width=296,
            wrap=False,
            style=TextStyle(
                font_size=10,
                font=FontSpec("Helvetica-Bold"),
                tracking=140,
                fill=Color(0.23, 0.39, 0.75),
            ),
        ).render(x=384, top=366)
    )
    builder.add(
        TextBlock(
            id="catalog.landscape.title",
            name="Product title",
            text="Focus Lamp 02",
            width=296,
            wrap=False,
            style=TextStyle(
                font_size=30,
                font=FontSpec("Helvetica-Bold"),
                fill=Color(0.08, 0.1, 0.16),
            ),
        ).render(x=384, top=326)
    )
    builder.add(
        AreaTextBlock(
            id="catalog.landscape.description",
            name="Landscape product description",
            text=(
                "A compact task light designed for focused work. The linked image can be "
                "replaced independently, while this paragraph remains editable area text."
            ),
            width=296,
            height=96,
            style=TextStyle(
                font_size=11,
                font=FontSpec("Helvetica"),
                line_height_ratio=1.4,
                fill=Color(0.13, 0.16, 0.22),
            ),
        ).render(x=384, top=276)
    )
    builder.add_path(
        rectangle_path(
            "catalog.landscape.cta",
            name="CTA background",
            x=384,
            top=142,
            width=142,
            height=38,
            fill=Color(0.1, 0.18, 0.34),
        )
    )
    builder.add(
        TextBlock(
            id="catalog.landscape.cta-label",
            name="CTA label",
            text="VIEW DETAILS",
            width=118,
            alignment="center",
            wrap=False,
            style=TextStyle(
                font_size=10,
                font=FontSpec("Helvetica-Bold"),
                fill=Color(1, 1, 1),
            ),
        ).render(x=396, top=126)
    )
    layer = builder.build()
    return RenderedComponent(
        width=LANDSCAPE.width,
        height=LANDSCAPE.height,
        paths=layer.paths,
        text_frames=layer.text_frames,
        linked_images=layer.linked_images,
        item_order=layer.item_order,
    )


def render_portrait_card() -> RenderedComponent:
    builder = LayerBuilder(id="catalog.portrait.content", name=PORTRAIT.name)
    builder.add_path(
        rectangle_path(
            "catalog.portrait.background",
            name="Portrait card background",
            x=PORTRAIT.left,
            top=PORTRAIT.top,
            width=PORTRAIT.width,
            height=PORTRAIT.height,
            fill=Color(0.08, 0.11, 0.18),
        )
    )
    builder.add_image(portrait_image())
    builder.add(
        TextBlock(
            id="catalog.portrait.eyebrow",
            name="Category",
            text="STUDIO ESSENTIALS",
            width=262,
            wrap=False,
            style=TextStyle(
                font_size=9,
                font=FontSpec("Helvetica-Bold"),
                tracking=130,
                fill=Color(0.5, 0.68, 1),
            ),
        ).render(x=764, top=212)
    )
    builder.add(
        TextBlock(
            id="catalog.portrait.title",
            name="Product title",
            text="Focus Lamp 02",
            width=262,
            wrap=False,
            style=TextStyle(
                font_size=24,
                font=FontSpec("Helvetica-Bold"),
                fill=Color(1, 1, 1),
            ),
        ).render(x=764, top=180)
    )
    builder.add(
        AreaTextBlock(
            id="catalog.portrait.description",
            name="Portrait product description",
            text="Compact light, focused beam, and a replaceable linked image for every edition.",
            width=262,
            height=54,
            style=TextStyle(
                font_size=10,
                font=FontSpec("Helvetica"),
                line_height_ratio=1.35,
                fill=Color(0.78, 0.82, 0.9),
            ),
        ).render(x=764, top=138)
    )
    builder.add_path(
        rectangle_path(
            "catalog.portrait.cta",
            name="CTA background",
            x=764,
            top=72,
            width=126,
            height=32,
            fill=Color(0.5, 0.68, 1),
        )
    )
    builder.add(
        TextBlock(
            id="catalog.portrait.cta-label",
            name="CTA label",
            text="VIEW DETAILS",
            width=106,
            alignment="center",
            wrap=False,
            style=TextStyle(
                font_size=9,
                font=FontSpec("Helvetica-Bold"),
                fill=Color(0.05, 0.08, 0.14),
            ),
        ).render(x=774, top=58)
    )
    layer = builder.build()
    return RenderedComponent(
        width=PORTRAIT.width,
        height=PORTRAIT.height,
        paths=layer.paths,
        text_frames=layer.text_frames,
        linked_images=layer.linked_images,
        item_order=layer.item_order,
    )
