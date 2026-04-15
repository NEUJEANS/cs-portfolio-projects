# Static Site Generator Review — Pass 3

## Focus
End-to-end usability, docs alignment, and smoke-test realism.

## Findings
1. The README still implied `npm test` even though the project currently uses plain `node --test`.
2. The feature list did not mention the exact supported Markdown subset or hidden-page navigation behavior.

## Fixes applied
- Updated the README test command to `node --test test_static_site_generator.js`.
- Expanded the feature list to describe supported Markdown primitives and `nav: false` behavior.
- Re-ran unit tests and a CLI smoke test that generated an actual HTML page.

## Status
Pass complete; docs and behavior now match.
