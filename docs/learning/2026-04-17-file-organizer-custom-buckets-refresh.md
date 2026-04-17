# Node CLI refresh — file-organizer custom buckets — 2026-04-17

## Refreshed concepts
- A config-driven CLI should prefer a tiny, auditable JSON shape over an over-engineered DSL for a portfolio project.
- Custom rule precedence needs to be obvious; “custom first, defaults second” is easier to explain in demos than a hidden merge strategy.
- Safety rules should also apply to control files. If the config file lives inside the folder being organized, the tool should not move its own instructions away mid-run.
- `node:test` can cover most CLI safety cases here without adding a full integration-test framework.

## Quick self-test
- Could I explain why `.json` might belong in `datasets` instead of the fallback bucket for a specific user? Yes — the config lets the demo reflect a real workflow instead of one hard-coded taxonomy.
- Could I explain what `extendDefaults: false` does? Yes — it disables the built-in buckets so only the configured buckets plus the fallback bucket remain.
- Could I describe why duplicate custom-extension assignments should be rejected? Yes — silent precedence between two custom buckets would make the config surprising and harder to debug.
- Could I explain why undo does not need `--config`? Yes — undo replays the exact realized paths recorded in the manifest, so it should not depend on current categorization rules.
