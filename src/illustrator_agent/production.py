"""Repeatable end-to-end evidence for one reference production."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py_ai_illustrator.format import FileFormat, inspect_file
from py_ai_illustrator.illustrator import (
    materialize_native_ai,
    run_illustrator_modern_roundtrip_test,
    run_illustrator_test,
)
from py_ai_illustrator.legacy import dump_ai7, read_ai7
from py_ai_illustrator.model import Document, Group
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


def _contract_checks(
    evidence: dict[str, Any], contract: ProductionContract
) -> dict[str, bool]:
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


def _prepare_artifacts(
    output_directory: Path, production_id: str, *, include_illustrator: bool, force: bool
) -> dict[str, Path]:
    paths = {
        "legacy_ai": output_directory / f"{production_id}.ai",
        "ir": output_directory / f"{production_id}.ir.json",
        "legacy_preview": output_directory / f"{production_id}.preview.png",
        "report": output_directory / "report.json",
    }
    if include_illustrator:
        paths.update(
            {
                "native_ai": output_directory / f"{production_id}.native.ai",
                "native_preview": output_directory / f"{production_id}.native.preview.png",
            }
        )
    existing = [path for path in paths.values() if path.exists()]
    if existing and not force:
        names = ", ".join(path.name for path in existing)
        raise FileExistsError(f"refusing to overwrite existing M1 artifacts: {names}")
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


def run_reference_production(
    build_document: DocumentFactory,
    *,
    source: str | Path,
    input_data: str | Path,
    output_directory: str | Path,
    contract: ProductionContract,
    include_illustrator: bool = False,
    visual_accepted_by: str | None = None,
    force: bool = False,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Build one production and collect every available M1 acceptance artifact."""

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

    artifacts = _prepare_artifacts(
        output_path,
        contract.production_id,
        include_illustrator=include_illustrator,
        force=force,
    )
    document = build_document()
    second_document = build_document()
    source_determinism = semantic_diff(document, second_document)
    evidence = _document_evidence(document)
    contract_checks = _contract_checks(evidence, contract)

    artifacts["ir"].write_text(
        json.dumps(document.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dump_ai7(document, artifacts["legacy_ai"], source_base=source_path.parent)
    with tempfile.TemporaryDirectory(prefix="illustrator-agent-m1-") as temporary_directory:
        second_ai = Path(temporary_directory) / artifacts["legacy_ai"].name
        dump_ai7(second_document, second_ai, source_base=source_path.parent)
        ai_deterministic = artifacts["legacy_ai"].read_bytes() == second_ai.read_bytes()

    format_report = inspect_file(artifacts["legacy_ai"])
    parsed = read_ai7(artifacts["legacy_ai"])
    source_to_wire = semantic_diff(document, parsed.document)
    with tempfile.TemporaryDirectory(
        prefix="illustrator-agent-m1-canonical-"
    ) as temporary_directory:
        canonical_ai = Path(temporary_directory) / artifacts["legacy_ai"].name
        dump_ai7(parsed.document, canonical_ai, source_base=source_path.parent)
        canonical = read_ai7(canonical_ai)
        roundtrip = semantic_diff(parsed.document, canonical.document)
    preview = render_preview(
        artifacts["legacy_ai"], artifacts["legacy_preview"], overwrite=False
    )
    automated_checks = {
        "source_is_deterministic": source_determinism.equal,
        "ai_is_byte_deterministic": ai_deterministic,
        "legacy_ai_detected": format_report.format is FileFormat.LEGACY_AI,
        "legacy_safe_to_reserialize": parsed.safe_to_reserialize,
        "canonical_semantic_roundtrip": roundtrip.equal,
        "preview_created": artifacts["legacy_preview"].is_file(),
        **contract_checks,
    }
    report: dict[str, Any] = {
        "profile": "illustrator-agent-reference-production-v1",
        "production_id": contract.production_id,
        "report_path": str(artifacts["report"]),
        "source": {"path": str(source_path), "sha256": _sha256(source_path)},
        "input": {"path": str(input_path), "sha256": _sha256(input_path)},
        "artifacts": {
            "legacy_ai": {
                "path": str(artifacts["legacy_ai"]),
                "sha256": _sha256(artifacts["legacy_ai"]),
            },
            "ir": {"path": str(artifacts["ir"]), "sha256": _sha256(artifacts["ir"])},
            "legacy_preview": {
                "path": str(artifacts["legacy_preview"]),
                "sha256": _sha256(artifacts["legacy_preview"]),
            },
        },
        "document_evidence": evidence,
        "automated": {
            "status": "passed" if all(automated_checks.values()) else "failed",
            "checks": automated_checks,
            "format": format_report.to_dict(),
            "compatibility": parsed.compatibility_report(),
            "source_determinism": source_determinism.to_dict(),
            "source_to_wire_normalization": source_to_wire.to_dict(),
            "canonical_semantic_roundtrip": roundtrip.to_dict(),
            "preview": preview.to_dict(),
        },
        "illustrator": {"status": "not-run"},
        "visual_acceptance": {
            "status": "passed" if visual_accepted_by is not None else "pending",
            "accepted_by": visual_accepted_by,
            "criteria": list(contract.visual_acceptance),
        },
    }

    if include_illustrator:
        legacy_test = run_illustrator_test(artifacts["legacy_ai"], timeout=timeout)
        materialization = materialize_native_ai(
            artifacts["legacy_ai"], artifacts["native_ai"], timeout=timeout
        )
        native_format: dict[str, Any] | None = None
        native_preview: dict[str, Any] | None = None
        modern_roundtrip: dict[str, Any] | None = None
        if materialization.get("status") == "passed":
            inspected_native = inspect_file(artifacts["native_ai"])
            native_format = inspected_native.to_dict()
            rendered_native = render_preview(
                artifacts["native_ai"], artifacts["native_preview"], overwrite=False
            )
            native_preview = rendered_native.to_dict()
            modern_roundtrip = run_illustrator_modern_roundtrip_test(
                artifacts["native_ai"], timeout=timeout
            )
            report["artifacts"].update(
                {
                    "native_ai": {
                        "path": str(artifacts["native_ai"]),
                        "sha256": _sha256(artifacts["native_ai"]),
                    },
                    "native_preview": {
                        "path": str(artifacts["native_preview"]),
                        "sha256": _sha256(artifacts["native_preview"]),
                    },
                }
            )
        illustrator_checks = {
            "legacy_structure": legacy_test.get("status") == "passed",
            "native_materialization": materialization.get("status") == "passed",
            "native_ai_detected": native_format is not None
            and native_format.get("format") == FileFormat.PDF_COMPATIBLE_AI.value,
            "native_preview_created": artifacts["native_preview"].is_file(),
            "native_reopen_editability": modern_roundtrip is not None
            and modern_roundtrip.get("status") == "passed",
        }
        report["illustrator"] = {
            "status": "passed" if all(illustrator_checks.values()) else "failed",
            "checks": illustrator_checks,
            "legacy_structure": legacy_test,
            "native_materialization": materialization,
            "native_format": native_format,
            "native_preview": native_preview,
            "native_roundtrip": modern_roundtrip,
        }

    if report["automated"]["status"] != "passed":
        report["status"] = "failed"
    elif not include_illustrator:
        report["status"] = "awaiting-illustrator"
    elif report["illustrator"]["status"] != "passed":
        report["status"] = "failed"
    elif visual_accepted_by is not None:
        report["status"] = "passed"
    else:
        report["status"] = "awaiting-visual-acceptance"
    _write_report(artifacts["report"], report)
    return report
