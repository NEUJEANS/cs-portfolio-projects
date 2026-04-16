# 2026-04-16 distributed snapshot SVG assets refresh

## Quick refresh
- SVG is a strong documentation format for portfolio artifacts because it is text-based, diffable, and embeddable in Markdown without storing binary screenshots.
- A generated asset should be driven from structured simulation results, not scraped from rendered Markdown, so tests can lock in the output contract.
- Relative asset links should be computed from the Markdown output path so committed walkthrough files keep working after regeneration.

## Self-test
1. **Why start with SVG instead of PNG?**  
   SVG keeps the export deterministic and dependency-light while still working well for GitHub docs and many slide tools.

2. **What should each generated snapshot asset include?**  
   Process lanes, transfers, failure/recovery notes, marker arrows, and a summary block with balances, statuses, recorded in-flight messages, and totals.

3. **Why link SVG files from the walkthrough instead of inlining huge blobs?**  
   Separate asset files stay reusable across README/docs/pages, keep the Markdown readable, and make regeneration/resume flows cleaner.
