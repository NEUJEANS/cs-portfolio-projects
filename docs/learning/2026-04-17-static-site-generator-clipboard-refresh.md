# 2026-04-17 static-site-generator clipboard/accessibility refresh

## Brief research takeaways
- MDN `Clipboard.writeText()` notes that async clipboard writes are broadly available but only in secure contexts and can fail with permission-related errors.
- MDN ARIA live-region guidance recommends `aria-live="polite"` for non-urgent status updates so screen readers announce them without interrupting other speech.

## Slice decisions
- prefer `navigator.clipboard.writeText()` first for modern HTTPS/localhost previews
- keep a legacy `document.execCommand('copy')` fallback so generated pages still have a best-effort copy path in older or less privileged contexts
- attach a per-code-block polite status region instead of assertive alerts, because copy success/failure is useful but not urgent
