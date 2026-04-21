# Two-phase commit lab learning note — 2026-04-21 — bundle presets

## Quick refresh / self-test
- Presets should reuse the existing scenario-tag normalization/filter path instead of inventing a second selection system, otherwise manual tags and saved bundles will drift.
- A saved preset is really metadata plus a tag bundle, so the safest implementation is to resolve the preset into tags first, then hand the result to the existing catalog generation flow.
- Not every saved bundle contains blocked incidents, so the catalog renderer should avoid teasing the incident dashboard when the selected subset has nothing for that dashboard to triage.

## Resulting implementation rule
- Resolve presets into the same filtered scenario-path list used by manual tag filters, then let the catalog/dashboard writers stay deterministic on top of that shared selection.
