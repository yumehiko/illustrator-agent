import pytest
from py_ai_illustrator.model import Color, LayerItemRef, LinkedImage

from illustrator_agent import (
    AffineTransform,
    LayerBuilder,
    RenderedComponent,
    Table,
    TableColumn,
    TextBlock,
    ellipse_path,
    rectangle_path,
)


def test_layer_builder_composes_components_and_rejects_duplicate_ids() -> None:
    builder = LayerBuilder(id="page", name="Page")
    background = rectangle_path(
        "background", x=0, top=100, width=120, height=80, fill=Color(1, 1, 1)
    )
    marker = ellipse_path(
        "marker", center_x=20, center_y=70, radius_x=8, radius_y=8, fill=Color(0.2, 0.4, 0.8)
    )
    text = TextBlock(id="label", text="Label", width=80).render(x=32, top=78)

    builder.add_path(background)
    builder.add_path(marker)
    builder.add(text)
    layer = builder.build()

    assert [reference.id for reference in layer.item_order] == [
        "background",
        "marker",
        "label.line-0",
    ]
    with pytest.raises(ValueError, match="Duplicate item id"):
        builder.add_path(background)


def test_table_can_render_as_a_composable_component() -> None:
    table = Table(id="small", columns=[TableColumn("name", "Name", 100)], rows=[{"name": "One"}])
    rendered = table.render(x=10, top=100)
    builder = LayerBuilder(id="page", name="Page")

    builder.add(rendered)

    assert rendered.width == 100
    assert rendered.height == table.height
    assert len(builder.build().item_order) == len(rendered.item_order)


def test_layer_builder_keeps_component_as_editable_group() -> None:
    rendered = TextBlock(id="label", text="Grouped", width=80).render(x=20, top=80)
    builder = LayerBuilder(id="page", name="Page")

    group = builder.add_grouped(rendered, group_id="product-card", group_name="Product Card")

    assert group.name == "Product Card"
    assert builder.build().item_order == [LayerItemRef("group", "product-card")]


def test_layer_builder_composes_and_translates_linked_images() -> None:
    image = LinkedImage(id="photo", source="photo.png", x=10, y=80, width=60, height=40)
    component = RenderedComponent(width=60, height=40, linked_images=[image])
    translated = component.transformed(AffineTransform.translation(20, -10))
    builder = LayerBuilder(id="page", name="Page")

    builder.add(translated)

    placed = builder.build().linked_images[0]
    assert (placed.x, placed.y, placed.width, placed.height) == (30, 70, 60, 40)
    assert builder.build().item_order == [LayerItemRef("image", "photo")]
