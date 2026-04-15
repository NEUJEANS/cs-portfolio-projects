# 2026-04-15 MinHash identifier normalization refresh

## Quick refresh
- For a portfolio-friendly source-code mode, normalize only non-keyword identifiers; keep operators, punctuation, numbers, and language keywords visible so structure is preserved.
- Python's `keyword.kwlist` is enough to avoid collapsing reserved words like `def`, `return`, and `if` into generic identifier placeholders.
- Resumable persisted indexes need to store normalization choices alongside `token_mode`, `shingle_size`, and hashing parameters.

## Self-test
1. Why not normalize every code token?
   - Because collapsing keywords and operators would erase control-flow and syntax structure that still matters for code-clone comparison.
2. Why should normalization be limited to `code` mode?
   - Word and character modes are not modeling programming-language identifiers, so the flag would be misleading there.
3. Why persist the flag in saved indexes?
   - So later refreshes and scans reuse the same fingerprinting strategy instead of mixing incompatible signatures.
