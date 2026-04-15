# 2026-04-15 — shamir-secret-sharing-lab research

## Goal
Build a small but strong portfolio project that demonstrates threshold cryptography without needing external dependencies.

## Notes
- Shamir secret sharing encodes the secret as the constant term of a random polynomial of degree `threshold - 1`.
- Any `threshold` points determine that polynomial; fewer points should reveal nothing useful about the secret.
- Finite-field arithmetic is required so interpolation stays exact and does not leak structure from ordinary integer arithmetic.
- Using GF(257) is convenient for a UTF-8 text demo because source bytes are in `0..255`, while share values can use `0..256` in JSON safely.
- Horner evaluation keeps the implementation compact, and Lagrange interpolation at `x = 0` is enough to recover the constant term byte by byte.

## Build slice chosen
Implement a text-secret CLI with JSON bundle persistence (`split`, `inspect`, `recover`) plus tests for round trips and malformed-share handling.
