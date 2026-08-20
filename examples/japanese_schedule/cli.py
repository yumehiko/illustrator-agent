"""Production entry point and contract for the Japanese schedule."""

from __future__ import annotations

from pathlib import Path

from examples.production_runner import ProductionRun, run_production_cli
from illustrator_agent.production import ProductionContract

from .document import DOCUMENT_SOURCE, build_document, build_layout_report
from .input import DEFAULT_INPUT, load_schedule_input

DEFAULT_OUTPUT = Path(__file__).parents[2] / "build" / "japanese-schedule"

PRODUCTION_CONTRACT = ProductionContract(
    production_id="japanese-schedule",
    width=560,
    height=380,
    layer_names=("日本語イベント日程",),
    path_count=15,
    text_count=18,
    group_count=1,
    required_ids=(
        "japanese-schedule",
        "event-schedule.group",
        "event-schedule.header.description",
        "event-schedule.row-1.description.line-0",
        "event-schedule.row-1.description.line-1",
    ),
    required_group_names=("日本語イベント日程表",),
    visual_acceptance=(
        "すべての日本語、英数字、句読点が欠落や置換なく読める",
        "各point textがセル境界を越えず、検証済みの改行位置で表示される",
        "表の階層、余白、featuredとnoticeのvariantが意図どおりである",
    ),
    required_fonts=("KozGoPr6N-Regular",),
    require_verified_text_layout=True,
)


def main(argv: list[str] | None = None) -> int:
    def prepare(input_path: Path | None) -> ProductionRun:
        assert input_path is not None
        schedule = load_schedule_input(input_path)
        return ProductionRun(
            build_document=lambda: build_document(schedule),
            source=DOCUMENT_SOURCE,
            input_data=input_path,
            contract=PRODUCTION_CONTRACT,
            text_layout_report=build_layout_report(schedule),
        )

    return run_production_cli(
        description=__doc__,
        default_input=DEFAULT_INPUT,
        default_output=DEFAULT_OUTPUT,
        prepare=prepare,
        argv=argv,
    )
