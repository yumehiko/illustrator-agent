# New production

Read this reference only when Python source and explicit inputs are the source of truth.

## Start from maintained code

Use the public exports in [`src/illustrator_agent/__init__.py`](../../../src/illustrator_agent/__init__.py)
and adapt the nearest production example. Do not copy low-level implementation out of
`py-ai-illustrator`.

| Need | Production example |
| --- | --- |
| Theme, reusable components, chart, point text | [`examples/quarterly_kpi_report/`](../../../examples/quarterly_kpi_report/) |
| Table, Japanese font-aware measurement, wrapping, overflow | [`examples/japanese_schedule/`](../../../examples/japanese_schedule/) |
| Linked images, area text, multiple artboards | [`examples/product_catalog/`](../../../examples/product_catalog/) |
| JSON-driven variants, stable identity, artboard mapping | [`examples/campaign_variants/`](../../../examples/campaign_variants/) |

Use [`examples/production_runner.py`](../../../examples/production_runner.py) for CLI behavior and
[`src/illustrator_agent/production_contract.py`](../../../src/illustrator_agent/production_contract.py)
for the contract schema. Examples and tests, rather than prose documentation, are the detailed API
source of truth.

## Production contract

1. Validate all external content before document construction. Use explicit immutable domain data;
   reject missing, malformed, non-finite, duplicate, and inconsistent values at their input path.
2. Assign stable semantic identities before rendering. Derive repeated-item identities from stable
   keys, never list position; reject duplicate or invalid keys.
3. Declare font PostScript names and layout evidence where typography depends on them. Treat
   approximate measurement as insufficient for fail-closed production. Declare whether linked
   images remain linked and resolve their sources relative to the production source. Font catalog
   availability does not prove glyph coverage: if native compile or reopen reports substitution or
   a font mismatch, fail the gate. Before rerunning, explicitly resolve as a user requirement
   whether to change the font requirement, copy, or intended fallback policy; do not silently
   substitute a font.
4. Build a deterministic editable `Document` through public design-model APIs. Keep composition,
   geometry, typography, layout, and tables in their existing responsibility boundaries.
5. Define a `ProductionContract` with canvas/layers/counts, required identities and group names,
   applicable artboards, variants, linked images, area text, required fonts, and concrete visual
   acceptance criteria.

## Gates and output

Run the pure gate before trusting native output:

```python
from illustrator_agent.production import verify_reference_document

evidence = verify_reference_document(build_document, contract=PRODUCTION_CONTRACT)
```

Require `status == "passed"` and review every check. Supply verified text-layout evidence when the
contract requires it.

Run the chosen production module with locked dependencies and a new revision path:

```bash
uv run --locked python -m examples.<production_package> \
  --output-dir build/<production-id>-<revision>
```

The shared runner calls `compile_reference_production`, which repeats the pure gate, compiles native
AI, reopens and inspects it in Illustrator, checks requested fonts, and renders a preview. It writes
the native `.ai`, IR JSON, preview PNG, and `report.json`. A run without recorded human review must
remain `awaiting-visual-acceptance`; inspect the preview against every contract criterion before
recording an approver. Use `--force` only when the exact generated output set is deliberately being
regenerated and overwrite is explicitly intended.

Do not equate unit tests or a passed pure report with native compile/reopen, preview, font catalog,
or visual acceptance. If Illustrator is unavailable, preserve that state and hand off the exact
command and criteria still to run.

## Completion evidence

Report the Python source and input paths, their hashes from `report.json`, output artifact paths,
pure status, each Illustrator check, preview path, visual acceptance criteria and approver/state,
plus any unrun or failed gate. A production result is complete only when the report status is
`passed`; `awaiting-visual-acceptance` is a usable handoff, not final acceptance.
