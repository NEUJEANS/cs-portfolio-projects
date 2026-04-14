# Huffman Compressor Review Pass 2 — 2026-04-14

## Focus
Archive validation and malformed-input handling.

## Issues found
- Invalid JSON headers would surface as raw parser exceptions instead of a project-level archive error.
- Truncated payloads were not rejected until later, making failure modes less explicit.

## Fix applied
- Wrapped header decoding/JSON parsing with clear `ValueError` messages.
- Validated required metadata fields and types.
- Rejected negative sizes, non-positive frequencies, and too-short encoded payloads.
- Added regression tests for invalid headers and truncated payloads.

## Result
- Stronger defensive behavior and clearer interview-ready error handling.
