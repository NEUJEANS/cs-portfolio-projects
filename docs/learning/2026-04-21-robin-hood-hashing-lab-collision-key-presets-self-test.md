# Self-test note — robin-hood-hashing-lab collision key preset slice

Date: 2026-04-21

## Refresh
- Rechecked that this project's benchmark pipeline has three layers: deterministic trial rows, pooled summary slices, and thin Markdown/HTML renderers.
- Reconfirmed that `key_profile` is about identifier shape, so collision pressure should be modeled as a separate benchmark preset instead of overloading the profile concept.
- Reconfirmed that PNG sizing is driven from summary dimensions, so any new benchmark axis has to update the screenshot-height heuristic too.

## Quick self-test
- Added parser coverage for `--key-presets` alias normalization plus invalid-preset rejection.
- Added generator coverage confirming collision-focused keys really land in the chosen hotspot home slots.
- Extended benchmark summary and CLI coverage so `key_preset` flows through CSV/JSON rows, Markdown/HTML rendering, and dense PNG-height estimation.
- Extended the real CLI benchmark-flow test so the sample-style run now exercises both `uniform` and `collision-focused` presets across both key profiles.
