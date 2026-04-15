# 2026-04-15 Suffix Automaton Refresh

## Quick refresh
- each state represents an equivalence class of substrings sharing the same end-position set
- extending the automaton appends one character, updates suffix links, and creates a clone state only when a transition would otherwise violate the `len(p) + 1` invariant
- distinct substring count can be derived by summing `len(state) - len(link(state))` across non-root states
- occurrence counts need one reverse-length propagation pass after construction

## Self-test
- Why do clone states start with occurrence count `0`? Because they represent copied structure, not a newly seen end position.
- How is the longest repeated substring recovered? Pick the longest state whose propagated occurrence count meets the threshold, then slice the source text using its `first_pos`.
