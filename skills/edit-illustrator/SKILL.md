---
name: edit-illustrator
description: Create or revise editable Adobe Illustrator artwork from a design brief, source assets, or an existing .ai file. Use for banners, flyers, posters, catalogs, labels, tables, multi-size variants, text/color/image changes, and requests that require structured Illustrator output with validation and preview.
---

# Edit Illustrator

Create structured, editable Illustrator artwork through the public APIs of this repository and `py-ai-illustrator`. Preserve source files, report unsupported features, and verify the requested result before delivery.

## Workflow

1. Inspect the request, input files, dimensions, copy, assets, fonts, output names, and acceptance criteria.
2. Choose one source-of-truth path:
   - For new or repeatable work, create or revise a Python component/template.
   - For a local change to an existing `.ai`, inspect it and use a typed patch when supported.
3. Reuse `illustrator_agent` components and examples. Do not hand-edit Illustrator bytes or duplicate parsers and writers in the skill.
4. Keep semantic IDs and meaningful layer/group names. Make layout, font, color, crop, wrapping, and fallback policies explicit.
5. Generate to a new output path. Do not overwrite supplied artwork unless the user explicitly requests it.
6. Validate with `py-ai-illustrator`; use semantic diff and preview or visual diff in proportion to the change.
7. Report the output, source of truth, checks performed, unsupported or lossy behavior, and any remaining Illustrator-only verification.

## Capability Boundary

- Treat `py-ai-illustrator` feature profiles as the authority for supported `.ai` operations.
- Never infer that a successfully parsed modern AI file can be safely rewritten in full.
- Do not infer high-level components from arbitrary artwork without stable IDs, metadata, source Python, or another explicit mapping.
- If the request needs a missing Layer 1 feature, stop that operation and formulate a requirement with a fixture, exact operation, preservation constraints, and verification criteria.

## Repository References

Read these only as needed:

- `../../docs/design-model.md` for the render contract and dependency boundary.
- `../../examples/` for working production-style components.
