# Shamir authenticated share bundles research — 2026-04-15

## Goal
Add a meaningful integrity/authentication slice to the Shamir Secret Sharing lab so share bundles can detect tampering before recovery.

## Brief notes
- Shamir splitting alone gives confidentiality/threshold recovery, but not authenticity; altered share payloads can cause recovery failure or corrupted output.
- A practical, portfolio-friendly improvement is to authenticate the serialized share bundle with an HMAC derived from a user-supplied passphrase.
- `hashlib.pbkdf2_hmac` is in the Python standard library and provides a simple way to derive an HMAC key from a passphrase plus random salt.
- Using a canonical JSON payload (sorted keys, compact separators) avoids verification failures caused by formatting differences.
- Inspect/recover should verify authenticated bundles explicitly rather than silently ignoring the tag.

## Implementation choice
- Optional authenticated bundles via `--auth-passphrase` on `split`
- Store `{kdf, hash, iterations, salt_hex, tag_hex}` under `authentication`
- Verify on `recover` and optionally on `inspect --auth-passphrase ...`
- Refuse recovery from authenticated bundles when no passphrase is supplied

## Why this slice is good for the portfolio
- shows secure-by-default thinking beyond the base algorithm
- demonstrates key derivation, canonical serialization, and integrity verification
- adds a realistic story: splitting secrets for backup while detecting tampered storage
