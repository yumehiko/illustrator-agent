"""Native-first production orchestration for reference artwork."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from py_ai_illustrator.illustrator import list_illustrator_fonts, run_illustrator_test
from py_ai_illustrator.native import compile_native_ai
from py_ai_illustrator.verification import render_preview

from .production_contract import (
    ArtboardVariantContract,
    DocumentFactory,
    ProductionAreaText,
    ProductionArtboard,
    ProductionContract,
    ProductionLinkedImage,
)
from .production_dom import illustrator_contract_checks
from .production_verification import (
    evaluate_reference_document,
    verify_reference_document,
)

__all__ = [
    "ArtboardVariantContract",
    "ProductionAreaText",
    "ProductionArtboard",
    "ProductionContract",
    "ProductionLinkedImage",
    "compile_reference_production",
    "verify_reference_document",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_artifacts(
    output_directory: Path, production_id: str, *, force: bool
) -> dict[str, Path]:
    paths = {
        "native_ai": output_directory / f"{production_id}.native.ai",
        "ir": output_directory / f"{production_id}.ir.json",
        "native_preview": output_directory / f"{production_id}.native.preview.png",
        "report": output_directory / "report.json",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not force:
        names = ", ".join(path.name for path in existing)
        raise FileExistsError(f"refusing to overwrite existing production artifacts: {names}")
    if force:
        for path in existing:
            path.unlink()
    output_directory.mkdir(parents=True, exist_ok=True)
    return paths


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _font_result(contract: ProductionContract) -> dict[str, Any]:
    return {
        "status": "not-run" if contract.required_fonts else "not-required",
        "required": list(contract.required_fonts),
        "missing": [],
        "error": None,
    }


def compile_reference_production(
    build_document: DocumentFactory,
    *,
    source: str | Path,
    input_data: str | Path,
    output_directory: str | Path,
    contract: ProductionContract,
    text_layout_report: Mapping[str, Any] | None = None,
    visual_accepted_by: str | None = None,
    force: bool = False,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Compile a reference Document directly to verified native Illustrator AI."""

    source_path = Path(source).resolve()
    input_path = Path(input_data).resolve()
    output_path = Path(output_directory).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"production source does not exist: {source_path}")
    if not input_path.is_file():
        raise FileNotFoundError(f"production input does not exist: {input_path}")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if visual_accepted_by is not None and not visual_accepted_by.strip():
        raise ValueError("visual_accepted_by must not be empty")

    artifacts = _prepare_artifacts(output_path, contract.production_id, force=force)
    document, pure = evaluate_reference_document(
        build_document,
        contract,
        text_layout_report,
    )
    artifacts["ir"].write_text(
        json.dumps(document.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    compile_result: dict[str, Any] = {"status": "not-run"}
    inspection_result: dict[str, Any] = {"status": "not-run"}
    preview_result: dict[str, Any] | None = None
    font_result = _font_result(contract)
    if pure["status"] == "passed" and contract.required_fonts:
        raw_font_result = list_illustrator_fonts(
            query=contract.required_fonts[0] if len(contract.required_fonts) == 1 else None,
            required=contract.required_fonts,
            timeout=min(timeout, 30.0),
        )
        font_result = {
            "status": raw_font_result.get("status"),
            "illustrator_version": raw_font_result.get("illustrator_version"),
            "required": list(contract.required_fonts),
            "missing": raw_font_result.get("missing", []),
            "error": raw_font_result.get("error"),
        }
    fonts_available = font_result["status"] in {"passed", "not-required"}
    if pure["status"] == "passed" and fonts_available:
        compile_result = compile_native_ai(
            document,
            artifacts["native_ai"],
            source_base=source_path.parent,
            timeout=timeout,
        )
        if compile_result.get("status") == "passed":
            inspection_result = run_illustrator_test(
                artifacts["native_ai"],
                timeout=timeout,
            )
            preview_result = render_preview(
                artifacts["native_ai"],
                artifacts["native_preview"],
                timeout=timeout,
                overwrite=False,
            ).to_dict()

    native_checks = {
        "direct_native_compile": compile_result.get("status") == "passed",
        "reopen_semantic_editability": compile_result.get("status") == "passed"
        and bool(compile_result.get("illustrator", {}).get("ok")),
        "pdf_preview_created": preview_result is not None
        and artifacts["native_preview"].is_file(),
        "requested_fonts_available": fonts_available,
        **illustrator_contract_checks(inspection_result, contract),
    }
    visual = {
        "status": "passed" if visual_accepted_by is not None else "pending",
        "accepted_by": visual_accepted_by,
        "criteria": list(contract.visual_acceptance),
    }
    if pure["status"] != "passed" or not all(native_checks.values()):
        status = "failed"
    elif visual_accepted_by is None:
        status = "awaiting-visual-acceptance"
    else:
        status = "passed"

    artifact_report: dict[str, Any] = {
        "ir": {"path": str(artifacts["ir"]), "sha256": _sha256(artifacts["ir"])}
    }
    if artifacts["native_ai"].is_file():
        artifact_report["native_ai"] = {
            "path": str(artifacts["native_ai"]),
            "sha256": _sha256(artifacts["native_ai"]),
        }
    if artifacts["native_preview"].is_file():
        artifact_report["native_preview"] = {
            "path": str(artifacts["native_preview"]),
            "sha256": _sha256(artifacts["native_preview"]),
        }
    report = {
        "profile": "illustrator-agent-native-production-v1",
        "production_id": contract.production_id,
        "status": status,
        "report_path": str(artifacts["report"]),
        "source": {"path": str(source_path), "sha256": _sha256(source_path)},
        "input": {"path": str(input_path), "sha256": _sha256(input_path)},
        "artifacts": artifact_report,
        "pure": pure,
        "illustrator": {
            "status": "passed" if all(native_checks.values()) else "failed",
            "checks": native_checks,
            "compile": compile_result,
            "inspection": inspection_result,
            "preview": preview_result,
            "fonts": font_result,
        },
        "visual_acceptance": visual,
    }
    _write_report(artifacts["report"], report)
    return report
