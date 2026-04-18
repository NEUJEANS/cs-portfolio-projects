# CRDT OR-Set Lab — comparison preset-suite self-test (2026-04-18)

## Refresh prompt
- What exact scenario should show OR-Set beating naive timestamp ordering?
- What control case keeps the preset gallery honest instead of only showing divergence?
- What CLI ergonomics matter once built-in preset names exist?

## Answers
- A remove that only tombstones observed tags plus a concurrent/new add should leave OR-Set present while LWW can still drop the element if the remove timestamp dominates.
- A replica that first syncs the add and then removes it should make both OR-Set and LWW converge on the same final absence.
- Built-in preset names need discovery (`list-presets`) and friendly validation errors so a typo does not dump a Python traceback.

## Implementation check
- Added three built-in comparison presets: `concurrent-readd`, `unobserved-remove`, and `observed-remove-sync`.
- Added `compare-presets` suite generation for Markdown/HTML/JSON summary artifacts.
- Tightened the CLI error path so unknown preset names now surface as concise parser errors instead of raw tracebacks.
