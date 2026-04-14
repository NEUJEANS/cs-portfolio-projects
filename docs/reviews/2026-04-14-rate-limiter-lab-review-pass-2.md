# Review Pass 2 - Rate Limiter Lab

## Checks
- reviewed parameter validation paths
- checked JSON output for scripting friendliness
- inspected event parsing and ordering behavior

## Issues found
1. token bucket parameters needed explicit non-positive validation
2. needed confidence that inline events and file-based events compose predictably

## Fixes made
- kept explicit validation for `--rate` and `--capacity`
- kept merged event parsing sorted so simulation runs are deterministic
