# Review log — page-replacement WSClock frame-budget study slice

Date: 2026-04-19

## Pass 1 — code-path audit
### Findings
- The resumed local edit had broken newline escaping in the new CSV/text/SVG formatting helpers, which left the module with an unterminated string literal and prevented the new CLI from running.
- The new study path needed to keep per-frame adaptive window stats, mode summaries, and best-improvement metadata consistent with the single-frame comparison workflow.

### Fixes
- repaired the newline escaping in the new formatting helpers so the module parses cleanly again
- kept the `study-wsclock-modes` payload aligned with the existing comparison structure, including per-mode metrics, summary counts, and best adaptive gain metadata

## Pass 2 — docs and artifact audit
### Findings
- The project README documented single-frame adaptive comparisons, but not the new frame-budget sweep workflow or the new committed artifact bundle paths.
- The project checklist still treated multi-frame adaptive reporting as unfinished even though the implementation was now present.

### Fixes
- added a `study-wsclock-modes` command example plus explanatory copy to the README
- documented the committed `wsclock-frame-study` artifact bundles for both the adaptive-win and counterexample cases
- updated the project checklist and docs checklist to mark the frame-budget study slice as completed and point to the next dashboard/gallery follow-up

## Pass 3 — regression and artifact audit
### Findings
- The regression test for CSV export still expected the pre-fix adaptive minimum-window column value, so the suite failed even though the generated artifact matched the current bounded-window behavior.
- The new slice needed real artifact generation smoke tests, not just unit coverage.

### Fixes
- updated the CSV assertion to match the current adaptive minimum-window output
- reran `py_compile`, the full page-replacement unittest suite, and real `study-wsclock-modes` smoke commands for both committed benchmark bundles

## Result
The multi-frame adaptive WSClock reporting flow is now runnable, documented, backed by committed artifact bundles, and covered by regression tests plus real smoke runs.
