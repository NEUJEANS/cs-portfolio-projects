# Password Strength Auditor Refresh — 2026-04-14

## Quick refresh
- reviewed Python `argparse` patterns for optional flags
- refreshed `json.dumps(..., indent=2, sort_keys=True)` for deterministic CLI output
- confirmed subprocess-based CLI testing pattern with `subprocess.run(..., capture_output=True, text=True, check=True)`

## Self-test
- can explain why entropy should be paired with heuristics in a small password auditor
- can test both pure scoring logic and command-line output without extra dependencies
