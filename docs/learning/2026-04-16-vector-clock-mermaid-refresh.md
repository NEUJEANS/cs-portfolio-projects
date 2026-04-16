# 2026-04-16 vector clock Mermaid refresh + self-test

Refresh points:
- Vector clocks encode partial ordering, so concurrent versions should remain visible until an explicit merge strategy resolves them.
- A partition/heal demo is easier to understand when each write is attached to the replica that issued it and includes the resulting clock.
- Mermaid sequence diagrams use `participant` declarations and message arrows such as `A->>B: heal`.

Self-test:
1. Why not collapse concurrent versions before healing?  
   Because concurrency is exactly the condition we want to demonstrate; collapsing would hide the need for conflict resolution.
2. What should a post-heal diagram emphasize?  
   Divergent writes during isolation, the anti-entropy exchange after healing, and the causally newer merged version if one is produced.
3. Why generate Mermaid from structured simulation output instead of handwritten strings?  
   It stays deterministic, testable, and consistent with the JSON result already used by CLI tests.
