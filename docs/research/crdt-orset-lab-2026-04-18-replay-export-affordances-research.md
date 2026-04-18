# CRDT OR-Set Lab — replay export-affordances research (2026-04-18)

## Goal
Add static-host-friendly replay actions for copying checkpoint links and downloading a checkpoint as a standalone SVG card.

## Quick references checked
- MDN `Clipboard.writeText()`
- MDN `URL.createObjectURL()`
- MDN `HTMLAnchorElement.download`

## Notes pulled into the implementation
- `navigator.clipboard.writeText(...)` is the clean async path, but MDN documents it as secure-context-only, so local HTTP/file demos need a fallback.
- A hidden `<textarea>` plus `document.execCommand('copy')` still works as a pragmatic fallback for simple text-copy actions when the async clipboard API is unavailable.
- `URL.createObjectURL(new Blob(...))` plus a temporary `<a download>` is enough for client-side SVG export on a static page, as long as the blob URL is revoked after the click.
- The `download` attribute is only a hint, so the exported file name should already be safe and slugified before assigning it.

## Resulting product decision
- Keep exact-link and stable-sync-link copy buttons inside the replay page.
- Prefer async clipboard writes, then fall back to the hidden-textarea copy path.
- Generate the checkpoint SVG entirely in-browser and download it through a blob URL so the artifact stays fully static-hostable.
