# Mini MapReduce SVG chart refresh

## Refresher
- SVG `viewBox` lets the chart scale responsively while keeping deterministic coordinates in tests
- bar height should be computed from `value / max_value * chart_height`
- axis labels and `<title>` improve readability without adding JavaScript
- fixed dimensions plus centered bars keep reducer-count comparisons stable across runs

## Self-test before coding
Given chart height `168` and max value `84`:
- a bar for value `42` should render at half height = `84`
- a bar for value `84` should render at full height = `168`
- a bar for value `0` should render at height `0`

That contract is what the new timing/reducer-load SVG helpers implement.
