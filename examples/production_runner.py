"""Shared command-line runner for production-gated examples."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from examples import BUILD_ROOT
from illustrator_agent.production import ProductionContract, compile_reference_production
from illustrator_agent.production_contract import DocumentFactory


@dataclass(frozen=True, slots=True)
class ProductionRun:
    build_document: DocumentFactory
    source: Path
    input_data: Path
    contract: ProductionContract
    text_layout_report: Mapping[str, Any] | None = None


def run_production_cli(
    *,
    description: str,
    default_output: Path,
    prepare: Callable[[Path | None], ProductionRun],
    default_input: Path | None = None,
    argv: list[str] | None = None,
) -> int:
    """Parse shared options and execute one example's production contract."""

    parser = argparse.ArgumentParser(description=description)
    if default_input is not None:
        parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--accept-visual-by",
        help="record the human who approved the generated native preview",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    output_directory = args.output_dir.resolve()
    if not output_directory.is_relative_to(BUILD_ROOT.resolve()):
        raise ValueError(f"production output must be under {BUILD_ROOT}")

    run = prepare(getattr(args, "input", None))
    result = compile_reference_production(
        run.build_document,
        source=run.source,
        input_data=run.input_data,
        output_directory=output_directory,
        contract=run.contract,
        text_layout_report=run.text_layout_report,
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
