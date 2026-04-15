# 2026-04-15 static-site-generator asset pipeline review

## Review pass 1
- Found that the extra `sitegen.test.js` file was stale and failing against the current API.
- Fixed the suite to target the exported functions that actually exist and to verify the new asset/image behavior.

## Review pass 2
- Checked security-sensitive rendering paths.
- Confirmed image rendering now reuses `sanitizeHref` so `javascript:` URLs are blocked for both links and images.

## Review pass 3
- Reviewed portfolio framing and project docs.
- Updated the README to mention recursive asset copying and image support so the shipped feature set matches the implementation.
