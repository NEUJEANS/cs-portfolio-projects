# Research note — robin-hood-hashing-lab collision key preset slice

Date: 2026-04-21

## What I checked
- Tried a brief grounded web search for Robin Hood hashing collision-heavy benchmark ideas, but `web_search` hit a Gemini quota error (`429`) during this cron run.
- Rechecked the repo's current benchmark architecture instead: the project already separates identifier shape (`key_profile`) from workload shape (`workload`), so collision pressure fits best as another deterministic benchmark dimension rather than a new table implementation.
- Reviewed the current sample artifact bundle and report layout to confirm a new dimension would need to flow through raw rows, summaries, Markdown/HTML rendering, and PNG sizing.

## Decision
- Keep runtime keys string-only and keep `key_profile` focused on identifier shape.
- Add a separate `key_preset` dimension with `uniform` and `collision-focused` so the same string/integer identifiers can be replayed under both naturally spread hashes and hotspot-heavy home-slot pressure.
- Build the collision-focused preset by deterministically filtering candidate keys down to a small sampled hotspot set of home slots (`stable_hash(key) % capacity` in a chosen subset), which keeps the benchmark reproducible without weakening the main hash function.

## Why this slice is useful
- It turns the benchmark from “different key shapes” into “different clustering regimes,” which makes the interview story much stronger.
- It exercises both successful and unsuccessful lookups under intentional hotspot pressure, not just naturally uniform spread.
- It keeps the project scope tight: no typed table rewrite, no custom weak hash mode, just a reproducible workload generator layered onto the existing benchmark/report pipeline.
