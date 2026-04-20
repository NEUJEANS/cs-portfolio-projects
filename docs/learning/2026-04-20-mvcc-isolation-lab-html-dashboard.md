# MVCC isolation lab HTML dashboard refresh + self-test — 2026-04-20

## Quick refresh
- a useful static artifact page should answer three questions fast: what scenario is this, which modes stayed safe, and where do I click for deeper evidence
- relative links matter because committed artifacts may move together inside `docs/artifacts/`; the dashboard should not hard-code absolute paths
- abort counts alone can mislead when one mode fails due to an in-scenario assertion while others abort because of validation or lock conflicts

## Self-test
1. Why not embed absolute paths in the generated dashboard?
   - relative links keep the artifact portable across local checkout paths and GitHub-hosted static pages.
2. What detail was easy to miss in the repeatable-read scenario before the review pass?
   - `read-committed` aborted because the scenario assertion failed, not because of optimistic validation or locking.
3. What belongs in the hero area of a recruiter-facing artifact?
   - the scenario title/description plus quick footprint facts like transaction count, schedule ticks, and invariant count.

## Guardrails
- preserve existing Markdown and SVG exports; HTML is an optional companion artifact, not a replacement
- keep output deterministic so repeated exports hash the same
- make links and focus states obvious enough for keyboard navigation on a static page
