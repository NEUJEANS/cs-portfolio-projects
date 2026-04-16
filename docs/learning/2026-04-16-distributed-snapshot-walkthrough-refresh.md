# 2026-04-16 distributed snapshot walkthrough refresh

## Quick refresh
- GitHub renders Mermaid from fenced ```mermaid blocks, so keeping the export as Markdown preserves both readability and diffability.
- A walkthrough artifact should be generated from structured simulator output, not hand-assembled strings from ad hoc prints, so later slices stay reproducible.
- For partition/heal stories, the student-facing essentials are the ordered timeline, which links were down, which messages were still in flight, and whether the snapshot total stayed consistent.

## Self-test
1. **Why prefer Markdown + Mermaid over a static screenshot?**  
   Because the repo keeps a text artifact that renders on GitHub, stays easy to diff, and can be regenerated from the same scenario.

2. **What makes the walkthrough resumable?**  
   The export derives from the same scripted scenario result already used by tests, so rerunning the command recreates the artifact without manual cleanup.

3. **What should each snapshot section show?**  
   Initiator, balances, process status, down-link status, recorded in-flight channel messages, and the embedded Mermaid diagram.
