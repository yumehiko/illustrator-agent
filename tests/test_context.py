import pytest
from py_ai_illustrator.model import Color, Layer

from illustrator_agent import DesignTheme, DocumentContext, TextStyle


def test_design_theme_copies_roles_and_resolves_required_values() -> None:
    source_colors = {"ink": Color(0.1, 0.2, 0.3)}
    source_styles = {
        "heading": TextStyle(font_size=24, font_name="Helvetica-Bold", fill=source_colors["ink"])
    }

    theme = DesignTheme(colors=source_colors, text_styles=source_styles)
    source_colors["ink"] = Color(1, 1, 1)
    source_styles.clear()

    assert theme.color("ink") == Color(0.1, 0.2, 0.3)
    assert theme.text_style("heading").font_size == 24
    with pytest.raises(TypeError):
        theme.colors["ink"] = Color(0, 0, 0)  # type: ignore[index]


def test_design_theme_rejects_unknown_or_invalid_roles() -> None:
    theme = DesignTheme(colors={"ink": Color(0, 0, 0)}, text_styles={})

    with pytest.raises(KeyError, match="Unknown color role 'paper'.*ink"):
        theme.color("paper")
    with pytest.raises(KeyError, match="Unknown text style role 'body'.*none"):
        theme.text_style("body")
    with pytest.raises(ValueError, match="non-empty"):
        DesignTheme(colors={"": Color(0, 0, 0)}, text_styles={})
    with pytest.raises(TypeError, match="unsupported"):
        DesignTheme(colors={"ink": "black"}, text_styles={})  # type: ignore[dict-item]


def test_document_context_creates_an_isolated_document() -> None:
    metadata = {"business_case": "test", "tags": ["reference"]}
    context = DocumentContext(
        width=200,
        height=100,
        title="Context document",
        theme=DesignTheme(colors={}, text_styles={}),
        metadata=metadata,
    )
    layers = [Layer(id="content", name="Content")]

    document = context.create_document(layers)
    metadata["business_case"] = "changed"
    metadata["tags"].append("mutated")
    layers.clear()

    assert (document.width, document.height, document.title) == (200, 100, "Context document")
    assert document.metadata == {"business_case": "test", "tags": ["reference"]}
    assert [layer.id for layer in document.layers] == ["content"]
    assert context.unit == "pt"


@pytest.mark.parametrize(
    ("changes", "error_type", "message"),
    [
        ({"width": 0}, ValueError, "finite and positive"),
        ({"height": float("inf")}, ValueError, "finite and positive"),
        ({"title": ""}, ValueError, "title must not be empty"),
        ({"title": " Untitled"}, ValueError, "title must not be empty"),
        ({"theme": object()}, TypeError, "theme must be a DesignTheme"),
        ({"unit": "px"}, ValueError, "point units only"),
        ({"metadata": {"": "value"}}, ValueError, "metadata keys"),
        ({"metadata": {"value": float("nan")}}, ValueError, "numbers must be finite"),
        ({"metadata": {"value": object()}}, TypeError, "non-JSON value"),
    ],
)
def test_document_context_rejects_implicit_or_invalid_document_settings(
    changes: dict[str, object], error_type: type[Exception], message: str
) -> None:
    arguments = {
        "width": 200,
        "height": 100,
        "title": "Valid",
        "theme": DesignTheme(colors={}, text_styles={}),
        **changes,
    }

    with pytest.raises(error_type, match=message):
        DocumentContext(**arguments)  # type: ignore[arg-type]
