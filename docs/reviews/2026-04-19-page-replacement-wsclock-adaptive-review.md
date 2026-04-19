# Review log — page-replacement WSClock adaptive slice

Date: 2026-04-19

## Pass 1 — adaptive-schedule bounds audit
### Findings
- The first adaptive segment always started from the raw auto WSClock window, so an explicit `--max-window` cap did not apply until later segments.
- That broke the CLI contract by letting the adaptive schedule report `τ=6` even when the caller requested `--max-window 4`.

### Fixes
- clamped the initial adaptive window into the caller's `[min_window, max_window]` range before any segment output is emitted
- made the first-segment reason string say when the auto window was clamped

## Pass 2 — README / artifact audit
### Findings
- The new adaptive comparison workflow was visible in code and generated artifacts, but the README still lacked a dedicated command example, the new benchmark description, and the new artifact references.
- The README future-improvement list still described adaptive-vs-fixed comparison as unfinished even though this slice implemented it.

### Fixes
- added a dedicated `compare-wsclock-modes` example plus explanatory copy to the project README
- documented the `adaptive-phase-turnover` benchmark and the fixed-vs-adaptive artifact bundles
- updated interview notes and future-improvement bullets so the docs match the implemented feature set

## Pass 3 — regression audit
### Findings
- There was no regression test that locked down the explicit max-window clamp behavior for the first adaptive segment.
- A future refactor could reintroduce the out-of-bounds first-segment bug without breaking the existing comparison tests.

### Fixes
- added a regression test that exercises `compare_wsclock_modes(..., max_window=4)` and asserts the first adaptive segment stays within bounds and reports the clamp
- reran the full page-replacement unittest suite plus real smoke commands for both the adaptive-win and explicit-clamp scenarios

## Result
The adaptive WSClock slice now has a clearer CLI contract, matching docs/artifacts, and regression coverage for the subtle bounded-window edge case.
