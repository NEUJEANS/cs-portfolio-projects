# MinHash literal-normalization refresh

## Refresher
- The code tokenizer already emits identifiers, operators, and integer literals as separate tokens.
- A small targeted change is enough: normalize digits before identifier folding so numeric constants become a stable placeholder while keywords/operators remain intact.
- Any new code-mode flag must be rejected outside `--token-mode code` to keep CLI behavior obvious.

## Self-test before coding
- `normalize_text(..., token_mode="code", normalize_literals=True)` should turn `100` and `255` into the same token.
- Compare/build-index/benchmark JSON payloads should expose the new flag.
- Saved indexes must round-trip the new metadata without breaking refresh flows.
