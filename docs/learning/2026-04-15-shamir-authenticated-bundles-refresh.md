# Shamir authenticated bundles refresh — 2026-04-15

## Quick refresh
- `pbkdf2_hmac(digest, password, salt, iterations)` derives a stable secret key from a passphrase.
- `hmac.new(key, message, hashlib.sha256).hexdigest()` produces an authenticity tag.
- `hmac.compare_digest(a, b)` avoids timing-leak-prone string comparison.
- Canonical JSON for MAC input should use sorted keys and compact separators.

## Self-test
1. Why is a plain checksum insufficient for authenticated share bundles?
   - Because an attacker can modify both the shares and checksum; a keyed MAC prevents that.
2. Why exclude the authentication object itself from the MAC payload?
   - To avoid circularity; the tag should cover the underlying bundle contents.
3. What should recovery do if a bundle claims authentication but no passphrase is provided?
   - Refuse recovery so verification is never accidentally skipped.
