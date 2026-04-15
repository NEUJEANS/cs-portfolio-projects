# Review pass 1 — Chang-Roberts visualization export

## Focus
Mermaid renderer structure and likely parser compatibility.

## Findings
- Initial draft emitted a `Note over` line before declaring participants.
- Some Mermaid renderers are stricter about participant declarations appearing first.

## Fixes applied
- Reordered renderer output so all `participant` lines are declared before notes and message arrows.

## Status
- Re-ran the project test suite after the fix.
- Visualization-only CLI output now starts with participant declarations, then notes and edges.
