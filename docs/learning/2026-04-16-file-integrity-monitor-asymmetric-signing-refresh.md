# file-integrity-monitor asymmetric signing refresh — 2026-04-16

## Quick refresh
- `openssl dgst -sha256 -sign private.pem -out sig.bin payload.json` signs a payload with a PEM private key.
- `openssl dgst -sha256 -verify public.pem -signature sig.bin payload.json` verifies the detached signature with the matching public key.
- JSON signatures should be computed over a canonical payload; here that means the manifest without its `signature` field, serialized with sorted keys and compact separators.
- A stable `key_id` lets the verifier skip unrelated rotation candidates.

## Self-test
1. Generate a temporary RSA keypair.
2. Sign a canonicalized manifest with the private key.
3. Verify with the matching public key.
4. Verify that a different public key fails.
5. Confirm CLI flows still work for legacy HMAC signatures.

## Implementation decision
- Keep the project Python-standard-library-first.
- Add optional asymmetric support via the system `openssl` binary instead of introducing a Python crypto dependency.
- Preserve HMAC behavior for existing users and manifests.
