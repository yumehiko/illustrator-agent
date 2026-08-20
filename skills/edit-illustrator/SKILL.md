---
name: edit-illustrator
description: Create repeatable editable Illustrator artwork from explicit inputs, or make verified source-preserving local edits to existing .ai files. Use when the deliverable is an editable Adobe Illustrator file; do not use for generic raster editing or ordinary document tasks.
---

# Edit Illustrator

Produce an editable `.ai` artifact with evidence that matches the chosen source of truth.

## Choose the route

- For new artwork, repeatable variants, or a broad redesign, treat Python components/templates
  and explicit input data as the source of truth. Before changing files, read
  [New production](references/new-production.md).
- For a bounded change to an existing `.ai`, treat the original file as the source of truth.
  Before creating an operation manifest or running an edit command, read
  [Local AI edit](references/local-ai-edit.md).
- If a requested existing-file change cannot be expressed as a supported local operation, stop.
  Do not infer high-level components from arbitrary modern AI or silently switch to reconstruction.

## Shared contract

Before writing, identify the source, explicit content/assets, acceptance criteria, and a fresh output
path under `build/`. Do not overwrite the input or an existing artifact implicitly.

Keep editable structure and declared policies for fonts, text layout, and linked images. Do not
silently flatten, outline text, substitute fonts, embed linked images, or use another lossy fallback.

Distinguish pure validation from gates that require a licensed, responsive Illustrator runtime.
Record a gate as passed only from its produced evidence. Report pending, failed, unavailable, and
not-run gates as such.

If the required operation is missing from `py-ai-illustrator`, do not implement its parser, writer,
low-level IR, or validation here. Stop and report:

- a real minimal `.ai` fixture and its provenance;
- the exact operation needed;
- bytes, editability, identities, and visual properties that must be preserved;
- the checks that would prove the operation safe.

Finish with the source of truth, output paths, validations and evidence, visual acceptance state,
and every remaining limitation or unrun Illustrator gate.
