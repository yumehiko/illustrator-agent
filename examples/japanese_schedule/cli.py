"""Production entry point and contract for the Japanese schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from illustrator_agent.production import ProductionContract, compile_reference_production

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--accept-visual-by")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    schedule = load_schedule_input(args.input)
    result = compile_reference_production(
        lambda: build_document(schedule),
        source=DOCUMENT_SOURCE,
        input_data=args.input,
        output_directory=args.output_dir,
        contract=PRODUCTION_CONTRACT,
        text_layout_report=build_layout_report(schedule),
        visual_accepted_by=args.accept_visual_by,
        force=args.force,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {"status": result["status"], "report": result["report_path"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["status"] in {"passed", "awaiting-visual-acceptance"} else 1
