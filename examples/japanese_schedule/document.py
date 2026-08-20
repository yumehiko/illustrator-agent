"""Thin composition for the Japanese schedule reference production."""

from __future__ import annotations

from pathlib import Path

from illustrator_agent import (
    Color,
    DesignTheme,
    Document,
    DocumentContext,
    FontSpec,
    LayerBuilder,
    OverflowPolicy,
    Table,
    TableColumn,
    TableStyle,
    TextStyle,
)

from .input import JapaneseScheduleInput, load_schedule_input

DOCUMENT_SOURCE = Path(__file__)


def _schedule_theme(schedule: JapaneseScheduleInput) -> DesignTheme:
    font = FontSpec(
        postscript_name=schedule.font.postscript_name,
        family=schedule.font.family,
        style=schedule.font.style,
    )
    colors = {
        "ink": Color(0.12, 0.14, 0.2),
        "header": Color(0.12, 0.15, 0.25),
        "paper": Color(1.0, 1.0, 1.0),
        "alternate": Color(0.96, 0.97, 0.99),
        "featured": Color(0.89, 0.95, 1.0),
        "notice": Color(1.0, 0.94, 0.75),
        "border": Color(0.65, 0.7, 0.78),
    }
    return DesignTheme(
        colors=colors,
        text_styles={
            "header": TextStyle(font_size=schedule.font.header_size, font=font),
            "body": TextStyle(font_size=schedule.font.body_size, font=font),
        },
    )


def _schedule_table(schedule: JapaneseScheduleInput, theme: DesignTheme) -> Table:
    header = theme.text_style("header")
    body = theme.text_style("body")
    return Table(
        id="event-schedule",
        columns=(
            TableColumn("time", "時刻", 74, alignment="right"),
            TableColumn("category", "区分", 112, alignment="center", wrap=True),
            TableColumn(
                "description",
                "内容",
                304,
                wrap=True,
                provisional_wrap_width=272,
            ),
        ),
        rows=tuple(
            {
                "time": row.time,
                "category": row.category,
                "description": row.description,
                "kind": row.kind,
            }
            for row in schedule.rows
        ),
        variant_key="kind",
        style=TableStyle(
            header_height=36,
            row_height=38,
            padding_x=11,
            padding_y=8,
            line_height_ratio=1.35,
            header_fill=theme.color("header"),
            body_fill=theme.color("paper"),
            alternate_fill=theme.color("alternate"),
            variant_fills={
                "featured": theme.color("featured"),
                "notice": theme.color("notice"),
            },
            header_text_color=theme.color("paper"),
            body_text_color=theme.color("ink"),
            border_color=theme.color("border"),
            border_width=0.8,
            header_font=header.font,
            body_font=body.font,
            header_font_size=header.font_size,
            body_font_size=body.font_size,
            header_tracking=schedule.font.header_tracking,
            body_tracking=schedule.font.body_tracking,
        ),
        text_measurer=schedule.recorded_measurer(),
        overflow_policy=OverflowPolicy.FAIL_CLOSED,
    )


def build_layout_report(schedule: JapaneseScheduleInput | None = None) -> dict[str, object]:
    schedule = schedule or load_schedule_input()
    theme = _schedule_theme(schedule)
    return _schedule_table(schedule, theme).layout_report()


def build_document(schedule: JapaneseScheduleInput | None = None) -> Document:
    schedule = schedule or load_schedule_input()
    theme = _schedule_theme(schedule)
    context = DocumentContext(
        width=560,
        height=380,
        title=schedule.title,
        theme=theme,
        metadata={
            "source": "examples/japanese_schedule/document.py",
            "business_case": "japanese-schedule",
            "font_postscript_name": schedule.font.postscript_name,
        },
    )
    table = _schedule_table(schedule, theme)
    builder = LayerBuilder(id="japanese-schedule", name="日本語イベント日程")
    builder.add_grouped(
        table.render(x=40, top=330),
        group_id="event-schedule.group",
        group_name="日本語イベント日程表",
    )
    return context.create_document([builder.build()])
