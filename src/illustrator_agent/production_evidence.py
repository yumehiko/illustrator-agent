"""Normalize production evidence without applying contract policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from py_ai_illustrator.model import Document, Group


def document_evidence(document: Document) -> dict[str, Any]:
    """Extract the stable Document facts included in production reports."""

    groups: list[Group] = []
    paths = []
    texts = []
    images = []
    group_descendant_ids: dict[str, list[str]] = {}
    group_names_by_id: dict[str, str | None] = {}

    def visit_group(group: Group) -> list[str]:
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
        descendants = [
            *(path.id for path in group.paths),
            *(text.id for text in group.text_frames),
            *(image.id for image in group.linked_images),
        ]
        for child in group.groups:
            descendants.append(child.id)
            descendants.extend(visit_group(child))
        group_descendant_ids[group.id] = descendants
        group_names_by_id[group.id] = group.name
        return descendants

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
        *(artboard.id for artboard in document.artboards),
        *(layer.id for layer in document.layers),
        *(group.id for group in groups),
        *(path.id for path in paths),
        *(text.id for text in texts),
        *(image.id for image in images),
    }
    point_text_signatures = sorted(
        (
            {
                "id": text.id,
                "text": text.text,
                "font_postscript_name": text.native_font_name or text.font_name,
                "font_size": text.font_size,
                "tracking": text.tracking,
            }
            for text in texts
            if text.area_width is None
        ),
        key=lambda signature: signature["id"],
    )
    return {
        "width": document.width,
        "height": document.height,
        "layer_names": [layer.name for layer in document.layers],
        "path_count": len(paths),
        "text_count": len(texts),
        "group_count": len(groups),
        "linked_image_count": len(images),
        "linked_images": [
            {
                "id": image.id,
                "source": image.source,
                "x": image.x,
                "y": image.y,
                "width": image.width,
                "height": image.height,
            }
            for image in images
        ],
        "area_texts": [
            {
                "id": text.id,
                "width": text.area_width,
                "height": text.area_height,
                "leading": text.leading,
                "font_name": text.native_font_name or text.font_name,
            }
            for text in texts
            if text.is_area_text
        ],
        "artboards": [
            {
                "id": artboard.id,
                "name": artboard.name,
                "left": artboard.left,
                "top": artboard.top,
                "width": artboard.width,
                "height": artboard.height,
            }
            for artboard in document.artboards
        ],
        "group_names": [group.name for group in groups],
        "group_names_by_id": group_names_by_id,
        "group_descendant_ids": group_descendant_ids,
        "font_postscript_names": sorted(
            {text.native_font_name or text.font_name for text in texts}
        ),
        "point_text_count": len(point_text_signatures),
        "point_text_signatures": point_text_signatures,
        "ids": sorted(ids),
    }


def verified_layout_signatures(
    text_layout_report: Mapping[str, Any] | None,
) -> list[dict[str, Any]] | None:
    """Return normalized signatures only for complete fail-closed layout evidence."""

    if text_layout_report is None or text_layout_report.get("status") != "verified-fit":
        return None
    if text_layout_report.get("policy") != "fail-closed":
        return None
    cells = text_layout_report.get("cells")
    if not isinstance(cells, list) or not cells:
        return None

    signatures: list[dict[str, Any]] = []
    for cell in cells:
        if (
            not isinstance(cell, dict)
            or cell.get("status") != "verified-fit"
            or cell.get("policy") != "fail-closed"
        ):
            return None
        lines = cell.get("lines")
        if not isinstance(lines, list) or not lines:
            return None
        for line in lines:
            if not isinstance(line, dict) or line.get("status") != "verified-fit":
                return None
            text_id = line.get("text_id")
            measurement = line.get("measurement")
            if not isinstance(text_id, str) or not text_id or not isinstance(measurement, dict):
                return None
            provenance = measurement.get("provenance")
            request = measurement.get("request")
            if (
                not isinstance(provenance, dict)
                or provenance.get("font_aware") is not True
                or not isinstance(request, dict)
            ):
                return None
            required = ("value", "font_postscript_name", "font_size", "tracking")
            if any(field not in request for field in required):
                return None
            if (
                not isinstance(request["value"], str)
                or not isinstance(request["font_postscript_name"], str)
                or isinstance(request["font_size"], bool)
                or not isinstance(request["font_size"], int | float)
                or isinstance(request["tracking"], bool)
                or not isinstance(request["tracking"], int | float)
            ):
                return None
            signatures.append(
                {
                    "id": text_id,
                    "text": request["value"],
                    "font_postscript_name": request["font_postscript_name"],
                    "font_size": request["font_size"],
                    "tracking": request["tracking"],
                }
            )
    if len({signature["id"] for signature in signatures}) != len(signatures):
        return None
    return sorted(signatures, key=lambda signature: signature["id"])
