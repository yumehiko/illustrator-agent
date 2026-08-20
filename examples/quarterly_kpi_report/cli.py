"""CLI and production contract for the quarterly KPI report."""

from __future__ import annotations

from pathlib import Path

from examples.production_runner import ProductionRun, run_production_cli
from illustrator_agent.production import ProductionContract

from .document import DOCUMENT_SOURCE, REPORT_CONTEXT, build_document
from .input import DEFAULT_INPUT, load_report_input

DEFAULT_OUTPUT = Path(__file__).parents[2] / "build" / "quarterly-kpi-report"

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
    def prepare(input_path: Path | None) -> ProductionRun:
        assert input_path is not None
        report_input = load_report_input(input_path)
        return ProductionRun(
            build_document=lambda: build_document(report_input),
            source=DOCUMENT_SOURCE,
            input_data=input_path,
            contract=PRODUCTION_CONTRACT,
        )

    return run_production_cli(
        description=__doc__,
        default_input=DEFAULT_INPUT,
        default_output=DEFAULT_OUTPUT,
        prepare=prepare,
        argv=argv,
    )
