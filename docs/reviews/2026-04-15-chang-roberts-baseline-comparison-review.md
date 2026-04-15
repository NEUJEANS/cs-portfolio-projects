# Review log — Chang-Roberts baseline comparison

## Pass 1 — API shape
- Checked that the new comparison mode stays mutually exclusive with existing CLI modes.
- Fixed output shaping so `--include-visualization` works for comparison mode without breaking existing single-result modes.

## Pass 2 — trace semantics
- Checked that the baseline trace remains presentation-friendly instead of pretending to be a full asynchronous implementation.
- Added explicit trace notes so viewers can see that the baseline is intentionally a teaching comparison.

## Pass 3 — test coverage
- Checked simulator, renderer, and CLI entry points.
- Initial test run exposed that the first baseline draft only circulated one pass of ids, which failed to demonstrate the intended message-cost gap.
- Fixed the baseline to circulate each candidate id across the full ring so the comparison now shows a clear reduction for Chang-Roberts.
- Added tests for leader agreement, message-count reduction, baseline rendering, and comparison-mode visualization payloads.
