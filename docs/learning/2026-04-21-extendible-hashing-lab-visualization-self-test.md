# extendible-hashing-lab visualization self-test — 2026-04-21

## Quick refresh
- self-contained SVG artifacts need explicit accessible-name wiring if they use `aria-labelledby`; the references should point at real IDs.
- SVG `<title>` is useful twice here: once for the root accessible name and again for row-level hover/tooltips when visible text is truncated.
- compact visualization cards are easier to browse on GitHub if long labels are truncated visually but still recoverable through hover text or the paired HTML tables.

## Self-test
1. **Q:** Why is `aria-labelledby="title desc"` weaker than emitting concrete generated IDs?
   **A:** Because `aria-labelledby` is supposed to reference real element IDs; without IDs the relationship is ambiguous and some assistive tooling may ignore it.
2. **Q:** Why add nested SVG `<title>` nodes to the step and row groups instead of just widening every card?
   **A:** Tooltips preserve the full detail for long keys while keeping the exported artifact compact enough to browse directly in GitHub or a README context.
3. **Q:** What should remain deterministic across repeated visualization exports of the same workload?
   **A:** The SVG/HTML bytes, because the workload, hash function, layout, and generated IDs are all derived deterministically from the same ordered operations.
