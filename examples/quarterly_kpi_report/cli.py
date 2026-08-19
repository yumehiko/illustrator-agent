"""CLI and production contract for the quarterly KPI report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from illustrator_agent.production import ProductionContract, compile_reference_production

from .document import DOCUMENT_SOURCE, REPORT_CONTEXT, build_document
from .input import DEFAULT_INPUT, load_report_input

DEFAULT_OUTPUT = Path(__file__).parents[2] / "build" / "m1"

PRODUCTION_CONTRACT = ProductionContract(
    production_id="quarterly-kpi-report",
    width=REPORT_CONTEXT.width,
    height=REPORT_CONTEXT.height,
    layer_names=("Quarterly KPI report",),
    path_count=17,
    text_count=24,
    group_count=4,
    required_ids=(
        "quarterly-report",
        "metric-1.group",
        "metric-2.group",
        "metric-3.group",
        "operating-index.group",
        "operating-index.actual",
        "operating-index.target",
        "report.title.line-0",
    ),
    required_group_names=(
        "Metric: Revenue",
        "Metric: Gross margin",
        "Metric: Retention",
        "Operating index chart",
    ),
    visual_acceptance=(
        "タイトル、3つのKPIカード、折れ線チャート、出典が見切れず読める",
        "見出し、KPI値、chartのvisual hierarchyと余白が意図どおりである",
        "actual、target、gridの線種・色・重なり順が意図どおりである",
    ),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--accept-visual-by",
        help="record the human who approved the generated native preview",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    report_input = load_report_input(args.input)
    result = compile_reference_production(
        lambda: build_document(report_input),
        source=DOCUMENT_SOURCE,
        input_data=args.input,
        output_directory=args.output_dir,
        contract=PRODUCTION_CONTRACT,
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
