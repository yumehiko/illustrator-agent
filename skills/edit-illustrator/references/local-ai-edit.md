# Local AI edit

Read this reference only for a bounded edit whose source of truth is an existing `.ai` file.

Use the locked `py-ai` CLI from `py-ai-illustrator`. Its current writable profiles are
`legacy-ai7-trusted-v1` and `modern-ai-synchronized-patch-v1`. Profile support is an implementation
capability, not a permanent product restriction.

## Inspect and specify

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

## Plan, apply, validate, diff

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

## Fail closed and report

Stop on an ambiguous or missing selector, stale digest, unsupported operation or representation,
inconsistent modern PDF/PrivateData representations, unexpected semantic change, visual impact
outside the target, validation failure, or existing output path. Do not bypass a stop reason with
flattening, outlining, font substitution, materialization, or another lossy conversion.

Report input and output digests and paths, feature profile, manifest, resolved targets, expected and
actual impacts, apply validation, container validation, semantic-diff state, visual-diff artifact,
and any stop reasons. A generated file without this evidence is not a verified local edit.
