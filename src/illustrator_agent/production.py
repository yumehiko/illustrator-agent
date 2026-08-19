"""Native-first production contract for reference artwork."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py_ai_illustrator.model import Document, Group
from py_ai_illustrator.native import compile_native_ai
from py_ai_illustrator.semantic import semantic_diff
from py_ai_illustrator.verification import render_preview

DocumentFactory = Callable[[], Document]


@dataclass(frozen=True, slots=True)
class ProductionContract:
    """Machine-checkable and human-checkable completion criteria."""

    production_id: str
    width: float
    height: float
    layer_names: tuple[str, ...]
    path_count: int
    text_count: int
    group_count: int
    required_ids: tuple[str, ...]
    required_group_names: tuple[str, ...]
    visual_acceptance: tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _document_evidence(document: Document) -> dict[str, Any]:
    groups: list[Group] = []
    paths = []
    texts = []
    images = []

    def visit_group(group: Group) -> None:
        groups.append(group)
        paths.extend(group.paths)
        paths.extend(path for compound in group.compound_paths for path in compound.paths)
        paths.extend(
            path
            for clipping in group.clipping_groups
            for path in (clipping.clipping_path, *clipping.paths)
        )
        texts.extend(group.text_frames)
        images.extend(group.linked_images)
        for child in group.groups:
            visit_group(child)

    for layer in document.layers:
        paths.extend(layer.paths)
        paths.extend(path for compound in layer.compound_paths for path in compound.paths)
        paths.extend(
            path
            for clipping in layer.clipping_groups
            for path in (clipping.clipping_path, *clipping.paths)
        )
        texts.extend(layer.text_frames)
        images.extend(layer.linked_images)
        for group in layer.groups:
            visit_group(group)
    ids = {
        *(layer.id for layer in document.layers),
        *(group.id for group in groups),
        *(path.id for path in paths),
        *(text.id for text in texts),
        *(image.id for image in images),
    }
    return {
        "width": document.width,
        "height": document.height,
        "layer_names": [layer.name for layer in document.layers],
        "path_count": len(paths),
        "text_count": len(texts),
        "group_count": len(groups),
        "linked_image_count": len(images),
        "group_names": [group.name for group in groups],
        "ids": sorted(ids),
    }


def _contract_checks(evidence: dict[str, Any], contract: ProductionContract) -> dict[str, bool]:
    ids = set(evidence["ids"])
    group_names = set(evidence["group_names"])
    return {
        "canvas_dimensions": (evidence["width"], evidence["height"])
        == (contract.width, contract.height),
        "layer_names": evidence["layer_names"] == list(contract.layer_names),
        "path_count": evidence["path_count"] == contract.path_count,
        "text_count": evidence["text_count"] == contract.text_count,
        "group_count": evidence["group_count"] == contract.group_count,
        "required_ids": set(contract.required_ids) <= ids,
        "required_group_names": set(contract.required_group_names) <= group_names,
    }


def _evaluate_reference_document(
    build_document: DocumentFactory, contract: ProductionContract
) -> tuple[Document, dict[str, Any]]:
    document = build_document()
    repeated = build_document()
    source_determinism = semantic_diff(document, repeated)
    encoded = json.dumps(document.to_dict(), ensure_ascii=False, sort_keys=True)
    reconstructed = Document.from_dict(json.loads(encoded))
    ir_roundtrip = semantic_diff(document, reconstructed)
    evidence = _document_evidence(document)
    checks = {
        "source_is_deterministic": source_determinism.equal,
        "ir_json_roundtrip": ir_roundtrip.equal,
        **_contract_checks(evidence, contract),
    }
    return document, {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "document_evidence": evidence,
        "source_determinism": source_determinism.to_dict(),
        "ir_json_roundtrip": ir_roundtrip.to_dict(),
    }


def verify_reference_document(
    build_document: DocumentFactory, *, contract: ProductionContract
) -> dict[str, Any]:
    """Run the pure Document, determinism, IR roundtrip, and contract gate."""

    _, evidence = _evaluate_reference_document(build_document, contract)
    return evidence


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


def compile_reference_production(
    build_document: DocumentFactory,
    *,
    source: str | Path,
    input_data: str | Path,
    output_directory: str | Path,
    contract: ProductionContract,
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
    document, pure = _evaluate_reference_document(build_document, contract)
    artifacts["ir"].write_text(
        json.dumps(document.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    compile_result: dict[str, Any] = {"status": "not-run"}
    preview_result: dict[str, Any] | None = None
    if pure["status"] == "passed":
        compile_result = compile_native_ai(
            document,
            artifacts["native_ai"],
            source_base=source_path.parent,
            timeout=timeout,
        )
        if compile_result.get("status") == "passed":
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
            "preview": preview_result,
        },
        "visual_acceptance": visual,
    }
    _write_report(artifacts["report"], report)
    return report
