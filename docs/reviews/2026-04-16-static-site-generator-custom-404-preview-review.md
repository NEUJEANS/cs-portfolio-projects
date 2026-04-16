# Static site generator custom 404 preview review

- Timestamp: 2026-04-16 16:54 UTC
- Project: `static-site-generator`
- Slice: custom `404.html` generation and friendly preview missing-route responses

## Review pass 1
- Checked whether preview-only placeholders were scoped tightly enough.
- Found issue: `{{requestedPath}}`/related placeholders were being interpolated for every HTML preview response, not just missing-route 404 responses.
- Fix: added an explicit `previewPlaceholders` option to `sendPreviewFile()` and enabled it only for preview 404 responses.
- Regression coverage: added a test that regular HTML routes keep `{{requestedPath}}` untouched.

## Review pass 2
- Checked robustness around odd/malformed request paths.
- Found issue: `decodeURIComponent()` inside `applyPreviewPlaceholders()` could throw on malformed escape sequences and crash preview handling.
- Fix: wrapped path decoding in a safe fallback so malformed encodings stay literal instead of throwing.
- Regression coverage: added a test for malformed escape sequences.

## Review pass 3
- Checked protocol behavior for non-body responses and missing-route edge cases.
- Found issue: plain-text fallback 404 responses still wrote a body for `HEAD` requests.
- Fix: made the no-custom-404 fallback return headers only for `HEAD` misses.
- Regression coverage: added a test that `HEAD` missing-route responses return status `404` with an empty body.

## Result
- Focused syntax check: `node --check sitegen.js`
- Focused test run: `node --test sitegen.test.js test_static_site_generator.js`
- Full project test run: `npm test`
- Status: all checks passing after the three review fixes.
