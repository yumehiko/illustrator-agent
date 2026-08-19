"""Composition of rendered components into editable layers and groups."""

from __future__ import annotations

from dataclasses import dataclass, field

from py_ai_illustrator.model import Group, Layer, LayerItemRef, LinkedImage, Path, TextFrame

from .transforms import (
    AffineTransform,
    transform_group,
    transform_image,
    transform_path,
    transform_text,
)


@dataclass(slots=True)
class RenderedComponent:
    """A component result that can be composed before becoming an IR layer."""

    width: float
    height: float
    paths: list[Path] = field(default_factory=list)
    text_frames: list[TextFrame] = field(default_factory=list)
    linked_images: list[LinkedImage] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)
    item_order: list[LayerItemRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("Rendered component dimensions must not be negative")
        if not self.item_order:
            self.item_order = [
                *(LayerItemRef("path", path.id) for path in self.paths),
                *(LayerItemRef("text", text.id) for text in self.text_frames),
                *(LayerItemRef("image", image.id) for image in self.linked_images),
                *(LayerItemRef("group", group.id) for group in self.groups),
            ]

    def as_layer(self, *, layer_id: str, layer_name: str) -> Layer:
        return Layer(
            id=layer_id,
            name=layer_name,
            paths=list(self.paths),
            text_frames=list(self.text_frames),
            linked_images=list(self.linked_images),
            groups=list(self.groups),
            item_order=list(self.item_order),
        )

    def as_group(self, *, group_id: str, group_name: str | None = None) -> Group:
        return Group(
            id=group_id,
            name=group_name,
            paths=list(self.paths),
            text_frames=list(self.text_frames),
            linked_images=list(self.linked_images),
            groups=list(self.groups),
            item_order=list(self.item_order),
        )

    def transformed(self, transform: AffineTransform) -> RenderedComponent:
        """Place a component without discarding editable child identities."""

        if (self.text_frames or self.linked_images) and not transform.is_rigid:
            raise ValueError(
                "Components containing text or images currently require a rigid transform"
            )
        width = abs(transform.a) * self.width + abs(transform.c) * self.height
        height = abs(transform.b) * self.width + abs(transform.d) * self.height
        return RenderedComponent(
            width=width,
            height=height,
            paths=[transform_path(path, transform) for path in self.paths],
            text_frames=[transform_text(text, transform) for text in self.text_frames],
            linked_images=[transform_image(image, transform) for image in self.linked_images],
            groups=[transform_group(group, transform) for group in self.groups],
            item_order=list(self.item_order),
        )


@dataclass(slots=True)
class LayerBuilder:
    """Compose independently rendered semantic components into one editable layer."""

    id: str
    name: str
    _paths: list[Path] = field(default_factory=list, init=False, repr=False)
    _text_frames: list[TextFrame] = field(default_factory=list, init=False, repr=False)
    _linked_images: list[LinkedImage] = field(default_factory=list, init=False, repr=False)
    _groups: list[Group] = field(default_factory=list, init=False, repr=False)
    _item_order: list[LayerItemRef] = field(default_factory=list, init=False, repr=False)
    _ids: set[str] = field(default_factory=set, init=False, repr=False)

    def _claim(self, item_id: str) -> None:
        if not item_id:
            raise ValueError(f"Item id in layer {self.id!r} must not be empty")
        if item_id in self._ids:
            raise ValueError(f"Duplicate item id in layer {self.id!r}: {item_id!r}")
        self._ids.add(item_id)

    def add_path(self, path: Path) -> None:
        self._claim(path.id)
        self._paths.append(path)
        self._item_order.append(LayerItemRef("path", path.id))

    def add_text(self, text: TextFrame) -> None:
        self._claim(text.id)
        self._text_frames.append(text)
        self._item_order.append(LayerItemRef("text", text.id))

    def add_image(self, image: LinkedImage) -> None:
        self._claim(image.id)
        self._linked_images.append(image)
        self._item_order.append(LayerItemRef("image", image.id))

    def add_group(self, group: Group) -> None:
        self._claim(group.id)
        self._groups.append(group)
        self._item_order.append(LayerItemRef("group", group.id))

    def add_grouped(
        self,
        component: RenderedComponent,
        *,
        group_id: str,
        group_name: str | None = None,
    ) -> Group:
        """Keep a rendered component movable as one editable Illustrator group."""

        group = component.as_group(group_id=group_id, group_name=group_name)
        self.add_group(group)
        return group

    def add(self, component: RenderedComponent) -> None:
        paths = {path.id: path for path in component.paths}
        text_frames = {text.id: text for text in component.text_frames}
        linked_images = {image.id: image for image in component.linked_images}
        groups = {group.id: group for group in component.groups}
        for reference in component.item_order:
            if reference.kind == "path":
                self.add_path(paths[reference.id])
            elif reference.kind == "text":
                self.add_text(text_frames[reference.id])
            elif reference.kind == "image":
                self.add_image(linked_images[reference.id])
            elif reference.kind == "group":
                self.add_group(groups[reference.id])
            else:
                raise ValueError(f"Rendered components do not yet support {reference.kind!r} items")

    def build(self) -> Layer:
        return Layer(
            id=self.id,
            name=self.name,
            paths=list(self._paths),
            text_frames=list(self._text_frames),
            linked_images=list(self._linked_images),
            groups=list(self._groups),
            item_order=list(self._item_order),
        )
