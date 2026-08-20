"""Agent-facing design components for editable Illustrator artwork."""

from py_ai_illustrator.model import Artboard, Color, Document, Group, LinkedImage

from .composition import LayerBuilder, RenderedComponent
from .context import DesignTheme, DocumentContext
from .geometry import ellipse_path, polyline_path, rectangle_path
from .identity import (
    ComponentIdentity,
    DuplicateSemanticKeyError,
    IdentityError,
    IdentityNamespace,
    StableIdentityCollisionError,
    validate_identity_segment,
)
from .images import fit_linked_image
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
from .text_layout import (
    APPROXIMATE_PROVENANCE,
    ApproximateTextMeasurer,
    MeasurementProvenance,
    MissingTextMeasurementError,
    OverflowPolicy,
    OverflowStatus,
    RecordedTextMeasurer,
    TextLayoutResult,
    TextMeasurement,
    TextMeasureRequest,
    TextOverflowError,
    estimate_text_width,
    evaluate_text_layout,
    wrap_text_approximately,
)
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
    "APPROXIMATE_PROVENANCE",
    "AreaTextBlock",
    "Artboard",
    "ApproximateTextMeasurer",
    "Color",
    "ComponentIdentity",
    "Contract",
    "DesignTheme",
    "Document",
    "DocumentContext",
    "DuplicateSemanticKeyError",
    "FontSpec",
    "Group",
    "IdentityError",
    "IdentityNamespace",
    "InputValidationError",
    "LayerBuilder",
    "LinkedImage",
    "MeasurementProvenance",
    "MissingTextMeasurementError",
    "OverflowPolicy",
    "OverflowStatus",
    "RecordedTextMeasurer",
    "RenderedComponent",
    "StableIdentityCollisionError",
    "Table",
    "TableColumn",
    "TableStyle",
    "TextBlock",
    "TextLayoutResult",
    "TextMeasurement",
    "TextMeasureRequest",
    "TextOverflowError",
    "TextStyle",
    "array_contract",
    "boolean",
    "ellipse_path",
    "evaluate_text_layout",
    "estimate_text_width",
    "field",
    "finite_number",
    "fit_linked_image",
    "non_empty_string",
    "object_contract",
    "polyline_path",
    "rectangle_path",
    "transform_group",
    "transform_image",
    "transform_path",
    "transform_text",
    "validate_identity_segment",
    "wrap_text_approximately",
]
