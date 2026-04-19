# Regex engine NFA trace research — 2026-04-19

## Brief source refresh
- Russ Cox's Thompson-NFA write-up is still the best compact reminder that the interesting runtime object is the active state set, not recursive backtracking call stacks.
- For a teaching-oriented lab, the most useful trace is therefore: current closure -> character consumed -> concrete matching transitions -> next closure.
- Search needs one extra layer beyond fullmatch: each candidate start offset should be visible so students can see why the leftmost match wins even when later starts would also work.

## Slice decision
Add JSON trace output instead of a graphical UI first.

Why this is the right next slice:
- it makes the existing engine more explainable without changing the supported regex language
- it improves interview/demo value because the runtime is now inspectable, not just correct
- it creates a clean base for future HTML/SVG teaching artifacts
