# Chord Graphviz review pass 3

## Focus
Output quality and DOT escaping.

## Findings
1. Route/stabilization labels originally emitted literal newlines, which made JSON output harder to inspect and was less explicit for DOT consumers.
2. DOT labels needed simple escaping for backslashes, quotes, and embedded newlines.

## Fixes applied
- Switched label formatting to explicit `\\n` sequences in DOT strings.
- Tightened `_dot_label()` escaping for safer Graphviz text emission.
- Re-ran the Chord test suite after the output cleanup.
