# CRDT OR-Set Visualization Refresh + Self-Test — 2026-04-18

## Quick refresh
- A good OR-Set visualization must show both **membership** and the underlying **tags/tombstones**, otherwise the "remove did not delete the later add" story is too hand-wavy.
- Mermaid sequence diagrams can cover replica-local add/remove operations with self-messages and cross-replica syncs with normal arrows plus `Note over` state summaries.
- A handcrafted SVG card does not need a full lane diagram to be useful; a clean step-by-step event card with final converged state is enough for README screenshots.

## Self-test
1. **What detail is essential after a remove step?**  
   Which observed tags were tombstoned, not just whether membership became empty on that replica.
2. **Why keep Markdown and Mermaid alongside SVG?**  
   Markdown is readable in plain text/code review, Mermaid is editable/portable, and SVG is screenshot-ready.
3. **Why generate all artifacts from the same snapshot object?**  
   So the portfolio exports stay consistent with the CLI JSON output and future review fixes only touch one source of truth.
