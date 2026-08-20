"""Agent-facing design components for editable Illustrator artwork."""

from py_ai_illustrator.model import Artboard, Color, Document, Group, LinkedImage

from .composition import LayerBuilder, RenderedComponent
from .context import DesignTheme, DocumentContext
from .geometry import ellipse_path, polyline_path, rectangle_path
from .input_contracts import (
    Contract,
    InputValidationError,
    array_contract,
    boolean,
    field,
    finite_number,
    non_empty_string,
    object_contract,
)
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
    "Contract",
    "DesignTheme",
    "Document",
    "DocumentContext",
    "FontSpec",
    "Group",
    "InputValidationError",
    "LayerBuilder",
    "LinkedImage",
    "RenderedComponent",
    "Table",
    "TableColumn",
    "TableStyle",
    "TextBlock",
    "TextStyle",
    "array_contract",
    "boolean",
    "ellipse_path",
    "estimate_text_width",
    "field",
    "finite_number",
    "non_empty_string",
    "object_contract",
    "polyline_path",
    "rectangle_path",
    "transform_group",
    "transform_image",
    "transform_path",
    "transform_text",
    "wrap_text_approximately",
]
