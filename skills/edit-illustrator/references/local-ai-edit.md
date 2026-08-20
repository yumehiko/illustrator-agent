# Local AI edit

Read this reference only for a bounded edit whose source of truth is an existing `.ai` file.

Use the locked `py-ai` CLI from `py-ai-illustrator`. Choose one of two routes before planning:

- the source-preserving pure route, with `legacy-ai7-trusted-v1` or
  `modern-ai-synchronized-patch-v1`;
- the licensed-runtime route, `illustrator-native-local-edit-v1`, for a bounded live text or linked
  image change that the pure inspection cannot prove safe.

These routes have different preservation guarantees. Missing pure selectors are a stop, not
permission to fall back. Select the native route explicitly only when current-format Illustrator
save-as is acceptable and the licensed runtime gates are required. Profile support is an
implementation capability, not a permanent product restriction.

## Source-preserving pure route

### Inspect and specify

Keep the original input unchanged. Choose new paths under `build/` for the operation manifest,
edited `.ai`, diff image, and captured reports.

```bash
uv run --locked py-ai inspect <input.ai> --json
```

Use only selectors and operations advertised by this inspection. A selector is conjunctive and
must resolve to exactly one target; copy stable `type` and `id` evidence when available. Do not
guess, broaden, fall back to fuzzy matching, or export and reconstruct a partial semantic model.

Create a versioned manifest with the current input's lowercase SHA-256 digest as a stale-source
precondition. Modern inspection emits `source_sha256`; for legacy AI, hash the exact input bytes
with the host's SHA-256 utility before writing the manifest:

```json
{
  "schema_version": 1,
  "source_sha256": "<64 lowercase hex characters>",
  "operations": [
    {
      "op": "replace_text",
      "selector": {"type": "text", "id": "<inspected-id>"},
      "text": "<replacement>"
    }
  ]
}
```

Supported requests are `set_fill`, `set_stroke`, `replace_text`, `translate`, and
`replace_linked_image_source`; the inspected target may support only a subset. Include all intended
changes in one atomic manifest when they must succeed together.

### Plan, apply, validate, diff

Follow this order without skipping a failed phase:

```bash
uv run --locked py-ai plan <input.ai> <operations.json>
uv run --locked py-ai apply <input.ai> <operations.json> --output <new-output.ai>
uv run --locked py-ai validate <new-output.ai>
uv run --locked py-ai diff <input.ai> <new-output.ai> --visual --output <new-diff.png>
```

Before apply, require the plan to report `applicable: true`, no stop reasons, the expected source
digest, one exact resolved target per operation, and impacts limited to the request. Re-inspect and
re-plan if the input digest changes. Apply only to a distinct path that does not exist.

Require apply to report `applied: true`, an unchanged source, and all returned preservation,
semantic-impact, and visual-bound validations true. Require `validate` to accept the written
container. Review the visual diff against the planned target bounds and requested result.

For legacy AI, also inspect the semantic diff:

```bash
uv run --locked py-ai diff <input.ai> <new-output.ai> --semantic
```

The standalone semantic diff supports legacy AI only. For modern AI, rely on the synchronized
patch profile's apply validations and the standalone visual diff; do not misreport an unsupported
semantic command as a successful gate.

## Illustrator-native local-edit route

Use `illustrator-native-local-edit-v1` only after choosing the licensed-runtime route explicitly.
It is not an extension or fallback of `modern-ai-synchronized-patch-v1`: Illustrator regenerates a
current-format PDF-compatible AI, so the source remains byte-identical but the output does not
promise source-prefix or unknown PrivateData byte preservation.

Start a fresh revision under `build/`, capture every JSON response, and run in this order:

```bash
uv run --locked py-ai inspect-native-local <input.ai>
uv run --locked py-ai plan-native-local <input.ai> <operations.json>
uv run --locked py-ai apply-native-local <input.ai> <operations.json> --output <new-output.ai>
uv run --locked py-ai validate <new-output.ai>
uv run --locked py-ai preview <new-output.ai> --output <new-preview.png>
```

Native inspection must advertise exactly one live `TextFrame` or `PlacedItem` for every requested
operation. Copy its stable `type` and `id`; do not borrow selectors from pure inspection. The
manifest requires the inspected `source_sha256`. For a linked asset, use an explicit existing path,
and keep `replace_text` and `replace_linked_image_source` in one atomic manifest when they define
one variant.

Before apply, require `applicable: true`, no stop reasons, one exact resolved target per operation,
the expected source and asset digests, and feature profile `illustrator-native-local-edit-v1` with
`licensed_runtime_required: true`. Apply already creates `<output-stem>-visual-diff.png`; do not
replace that evidence with an unrelated standalone diff.

Require `applied: true`, no stop reasons, all runtime and validation checks true, matching output
digest, and replacement-asset hashes stable before/after execution and before publish. In
particular, require save/reopen evidence for live text, font/style and no substitution, linked
external image and editability, non-target text/image/path fingerprints and document structure,
PDF-compatible container and PrivateData/PDF timestamp freshness, unchanged source bytes, and zero
changed pixels outside the allowed target rectangles. Require standalone container validation,
then inspect the preview and native visual-diff PNG before accepting the result.

If Illustrator is unlicensed, unavailable, times out, or any selector, asset, DOM, container,
timestamp, source, or visual-bound check fails, stop. Do not publish or treat a generated candidate
as evidence.

## Fail closed and report

Stop on an ambiguous or missing selector, stale digest, unsupported operation or representation,
inconsistent modern PDF/PrivateData representations, unexpected semantic change, visual impact
outside the target, validation failure, or existing output path. Do not bypass a stop reason with
flattening, outlining, font substitution, materialization, or another lossy conversion.

Report input and output digests and paths, feature profile, manifest, resolved targets, expected and
actual impacts, apply validation, container validation, semantic-diff state, visual-diff artifact,
preview and visual acceptance state, runtime gate state, and any stop reasons. A generated file
without this evidence is not a verified local edit.
