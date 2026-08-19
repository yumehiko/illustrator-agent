import pytest

from illustrator_agent import estimate_text_width, wrap_text_approximately


def test_width_estimate_is_deterministic_but_font_independent() -> None:
    assert estimate_text_width("MMMM", 10) == pytest.approx(34)
    assert estimate_text_width("日本", 10) == pytest.approx(20)


def test_approximate_wrap_preserves_explicit_paragraphs() -> None:
    assert wrap_text_approximately("One two\n三四", max_width=30, font_size=10) == (
        "One",
        "two",
        "三四",
    )


def test_approximate_wrap_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="max_width"):
        wrap_text_approximately("text", max_width=0, font_size=10)
