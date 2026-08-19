"""Agent-facing design components for editable Illustrator artwork."""

from py_ai_illustrator.model import Artboard, Color, Document, Group, LinkedImage

from .composition import LayerBuilder, RenderedComponent
from .context import DesignTheme, DocumentContext
from .geometry import ellipse_path, polyline_path, rectangle_path
from .tables import Table, TableColumn, TableStyle
from .text_layout import estimate_text_width, wrap_text_approximately
from .transforms import (
    AffineTransform,
    transform_group,
    transform_image,
    transform_path,
    transform_text,
)
from .typography import AreaTextBlock, FontSpec, TextBlock, TextStyle

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
    "estimate_text_width",
    "polyline_path",
    "rectangle_path",
    "transform_group",
    "transform_image",
    "transform_path",
    "transform_text",
    "wrap_text_approximately",
]
