# Mini MapReduce inspection source excerpt refresh

Date: 2026-04-16 03:46 UTC

## Goal
Add reviewer-friendly source anchors and code excerpts to `inspect-plugin` artifacts without changing execution behavior.

## Refresher
- `inspect.getsourcelines(fn)` returns both the source lines and the starting line number.
- A stable file anchor can be represented as `filename.py#Lstart-Lend`.
- Source excerpts are safest as plain text in JSON and fenced/preformatted blocks in Markdown/HTML.
- CSV should stay compact, so anchors fit better there than full source excerpts.

## Self-test
- If a function starts at line 7 and spans 7 source lines, the anchor should be `file.py#L7-L13`.
- If a hook is missing, both its anchor and excerpt should remain `None`.
- JSON can carry multiline excerpts directly; HTML should escape them inside `<pre><code>`.
