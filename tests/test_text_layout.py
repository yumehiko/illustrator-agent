import pytest

from illustrator_agent import (
    ApproximateTextMeasurer,
    MeasurementProvenance,
    OverflowPolicy,
    RecordedTextMeasurer,
    TextMeasurement,
    TextMeasureRequest,
    TextOverflowError,
    estimate_text_width,
    evaluate_text_layout,
    wrap_text_approximately,
)


def test_width_estimate_is_deterministic_but_font_independent() -> None:
    assert estimate_text_width("MMMM", 10) == pytest.approx(34)
    assert estimate_text_width("日本", 10) == pytest.approx(20)
    assert estimate_text_width("日本", 10, tracking=100) == pytest.approx(21)


def test_approximate_wrap_preserves_explicit_paragraphs() -> None:
    assert wrap_text_approximately("One two\n三四", max_width=30, font_size=10) == (
        "One",
        "two",
        "三四",
    )


def test_approximate_wrap_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="max_width"):
        wrap_text_approximately("text", max_width=0, font_size=10)


def test_approximation_never_becomes_a_verified_fit() -> None:
    result = evaluate_text_layout(
        "日本語",
        max_width=40,
        font_postscript_name="KozGoPr6N-Regular",
        font_size=10,
        tracking=20,
        measurer=ApproximateTextMeasurer(),
        policy=OverflowPolicy.FAIL_CLOSED,
    )

    assert result.status == "rejected-unverified"
    assert result.line_layouts[0].measurement.provenance.font_aware is False
    with pytest.raises(TextOverflowError, match="rejected-unverified"):
        result.require_renderable()


def test_fail_closed_rejects_a_reported_overflow_with_complete_request() -> None:
    request = TextMeasureRequest("日本語", "KozGoPr6N-Regular", 10, 20)
    measurement = TextMeasurement(
        request=request,
        width=41,
        provenance=MeasurementProvenance(
            method="font-bounds",
            font_aware=True,
            source="measurement fixture",
        ),
    )
    result = evaluate_text_layout(
        request.value,
        max_width=40,
        font_postscript_name=request.font_postscript_name,
        font_size=request.font_size,
        tracking=request.tracking,
        measurer=RecordedTextMeasurer((measurement,)),
        policy=OverflowPolicy.FAIL_CLOSED,
    )

    assert result.status == "rejected-overflow"
    assert result.line_layouts[0].measurement.request == request


def test_recorded_font_aware_evidence_can_verify_a_fit() -> None:
    request = TextMeasureRequest("句読点、。", "KozGoPr6N-Regular", 11, 0)
    measurement = TextMeasurement(
        request=request,
        width=55,
        provenance=MeasurementProvenance(
            method="adobe-illustrator-point-text-width",
            font_aware=True,
            source="Adobe Illustrator fixture",
        ),
    )
    result = evaluate_text_layout(
        request.value,
        max_width=60,
        font_postscript_name=request.font_postscript_name,
        font_size=request.font_size,
        tracking=request.tracking,
        wrap=False,
        measurer=RecordedTextMeasurer((measurement,)),
        policy=OverflowPolicy.FAIL_CLOSED,
    )

    assert result.status == "verified-fit"
    assert result.renderable is True
    evidence = result.to_dict()["lines"][0]["measurement"]
    assert evidence["request"]["font_postscript_name"] == "KozGoPr6N-Regular"
    assert evidence["provenance"]["method"] == "adobe-illustrator-point-text-width"
