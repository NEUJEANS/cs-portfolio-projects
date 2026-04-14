# Password Strength Auditor Upgrade Research — 2026-04-14

## Goal
Strengthen `password-strength-auditor`, which was one of the weaker portfolio entries because it only returned a basic rating with minimal explanation.

## Brief findings
- entropy alone is not enough because human-chosen passwords often contain predictable runs even when they mix character classes
- sequential patterns such as `1234`, `abcd`, and keyboard runs like `qwerty` are useful lightweight heuristics for a small educational estimator
- portfolio value improves when the tool explains scoring decisions and offers machine-readable output for automation

## Applied direction
- keep the implementation dependency-free and interview-friendly
- add a simple score breakdown, reason list, and suggestions
- detect repeated-character runs and common sequential patterns
- support `--json` so the project looks more complete as a CLI utility
