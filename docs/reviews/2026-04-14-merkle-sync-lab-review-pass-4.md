# merkle-sync-lab Review Pass 4 — sync-plan design

## Focus
- checked whether the new vertical slice adds portfolio value instead of just more code
- reviewed operation ordering so the generated plan reads like a believable sync engine
- verified that directory creation is emitted before file copy operations

## Issue found
- initial implementation needed stronger proof that nested directory creation stays ordered and resumable

## Fix applied
- kept parent directories sorted by depth/name before copy operations
- documented the plan output clearly in the project README
