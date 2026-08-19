"""Agent-facing design components for editable Illustrator artwork."""

from py_ai_illustrator.model import Artboard, Color, Document, Group, LinkedImage

from .authoring import (
    AffineTransform,
    AreaTextBlock,
    FontSpec,
    LayerBuilder,
    RenderedComponent,
    Table,
    TableColumn,
    TableStyle,
    TextBlock,
    TextStyle,
    ellipse_path,
    polyline_path,
    rectangle_path,
    transform_group,
    transform_image,
    transform_path,
    transform_text,
)
from .context import DesignTheme, DocumentContext

__all__ = [
    "AffineTransform",
    "AreaTextBlock",
    "Artboard",
    "Color",
    "DesignTheme",
    "Document",
    "DocumentContext",
    "FontSpec",
    "Group",
    "LayerBuilder",
    "LinkedImage",
    "RenderedComponent",
    "Table",
    "TableColumn",
    "TableStyle",
    "TextBlock",
    "TextStyle",
    "ellipse_path",
    "polyline_path",
    "rectangle_path",
    "transform_group",
    "transform_image",
    "transform_path",
    "transform_text",
]
