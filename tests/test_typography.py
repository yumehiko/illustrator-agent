import pytest

from illustrator_agent import AreaTextBlock, FontSpec, TextBlock, TextStyle


def test_text_block_wraps_and_uses_alignment_anchor() -> None:
    block = TextBlock(
        id="summary",
        text="Reusable semantic text wraps deterministically",
        width=110,
        alignment="right",
        style=TextStyle(font_size=10, line_height_ratio=1.4),
    )

    rendered = block.render(x=20, top=100)

    assert len(rendered.text_frames) > 1
    assert all(frame.x == 130 for frame in rendered.text_frames)
    assert all(frame.alignment == "right" for frame in rendered.text_frames)
    assert rendered.text_frames[1].y == pytest.approx(rendered.text_frames[0].y - 14)


def test_area_text_block_compiles_to_one_reflowable_frame() -> None:
    rendered = AreaTextBlock(
        id="article.body",
        name="Article body",
        text="A paragraph that Illustrator can reflow when its frame changes.",
        width=180,
        height=96,
        alignment="left",
        style=TextStyle(font_size=10, line_height_ratio=1.6),
    ).render(x=40, top=220)

    frame = rendered.text_frames[0]
    assert (rendered.width, rendered.height) == (180, 96)
    assert len(rendered.text_frames) == 1
    assert frame.is_area_text
    assert (frame.x, frame.y, frame.area_width, frame.area_height) == (40, 220, 180, 96)
    assert frame.leading == 16


def test_font_spec_uses_one_native_postscript_name() -> None:
    font = FontSpec(
        postscript_name="KozGoPr6N-Regular",
        family="小塚ゴシック Pr6N",
        style="R",
    )
    rendered = TextBlock(
        id="heading",
        text="見出し",
        width=100,
        wrap=False,
        style=TextStyle(font=font),
    ).render(x=10, top=80)

    assert rendered.text_frames[0].font_name == font.postscript_name
    assert rendered.text_frames[0].native_font_name is None


def test_font_spec_rejects_a_family_name_as_postscript_name() -> None:
    with pytest.raises(ValueError, match="PostScript"):
        FontSpec(postscript_name="Noto Sans JP")


def test_text_style_compiles_tracking_to_each_native_text_line() -> None:
    rendered = TextBlock(
        id="eyebrow",
        text="DESIGN\nSYSTEM",
        width=120,
        wrap=False,
        style=TextStyle(tracking=140),
    ).render(x=10, top=80)

    assert [frame.tracking for frame in rendered.text_frames] == [140, 140]
