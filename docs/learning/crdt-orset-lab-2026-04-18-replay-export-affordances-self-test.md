# CRDT OR-Set Lab — replay export-affordances self-test (2026-04-18)

## Refresh prompt
- Why can copy-to-clipboard fail on an otherwise valid static demo page?
- What is the simplest static-page path for downloading generated SVG content?
- What extra escape hazards appear when Python emits embedded JavaScript source?

## Answers
- `navigator.clipboard.writeText(...)` requires a secure context in many browsers, so plain HTTP/local demos need a fallback copy path.
- Blob URLs created with `URL.createObjectURL(...)` plus a temporary anchor with `download` are enough for client-side SVG export.
- Python string escaping can accidentally corrupt regex literals or JS string literals inside generated HTML, so embedded script output needs syntax-aware validation.

## Implementation check
- Added exact-link and stable-sync-link copy actions with async-clipboard + textarea fallback behavior.
- Added in-browser checkpoint SVG generation and download wiring with revocable blob URLs.
- Added a regression test that extracts the generated replay script and runs `node --check` so future embedded-JS syntax mistakes are caught before commit.
