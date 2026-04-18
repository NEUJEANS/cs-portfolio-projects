# CRDT OR-Set Lab — comparison preset-suite research (2026-04-18)

## Goal
Add a built-in portfolio-friendly preset suite that demonstrates both divergence-heavy OR-Set vs LWW cases and a control case with one command.

## Quick refresh
- Reused the repo's existing pattern of shipping committed sample JSON scripts plus generated Markdown/HTML/JSON artifacts rather than inventing an external preset registry.
- Kept the suite narrow: one preset reuses `sample_compare_ops.json`, one new preset highlights an unobserved remove, and one new preset acts as an observed-remove control.
- The summary artifact should answer the reviewer-facing question quickly: **when do observed-remove tags matter, and when do both models agree anyway?**

## Implementation notes pulled into the slice
- Treat presets as metadata objects (`name`, `title`, `description`, script path, replicas, LWW bias) so future detail-export bundles can reuse the same registry.
- Keep preset script paths project-relative in outputs so the committed artifacts stay portable on GitHub and static hosts.
- Summarize outcomes in one table/card gallery first; defer deep links into per-preset replay/timeline bundles to a later slice.

## Scope chosen
- built-in preset registry in `crdt_orset_lab.py`
- `list-presets` CLI for discoverability
- `compare-presets` CLI that emits suite Markdown/HTML/JSON artifacts
- two additional committed preset scripts (`unobserved-remove`, `observed-remove-sync`)

## Deferred
- per-preset detail pages linked from the suite cards
- another CRDT family comparison beyond OR-Set vs LWW
- bitmap export bundling for slides
