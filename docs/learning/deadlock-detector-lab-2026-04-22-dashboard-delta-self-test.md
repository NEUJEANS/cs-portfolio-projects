# Deadlock detector dashboard delta self-test

## Quick refresh
- The dashboard already explains one request trial, but a recruiter still needs one compact answer to "what changed between the granted and denied paths?"
- The fastest dashboard delta story is immediate slack spent, first runnable-set difference, and the denied-path blocking summary.
- A contrast request should stay optional so the dashboard still works for simpler single-request demos.

## Self-test
1. **When should the dashboard show the delta panel?**
   - only when both a primary Banker request input and a contrast Banker request input are provided

2. **What is the most important side-by-side signal in the sample pair?**
   - the granted path still leaves `P1` runnable immediately, while the denied path leaves no runnable process

3. **Why reuse the existing gallery delta builder instead of re-deriving the comparison in the dashboard renderer?**
   - so the JSON, Markdown, HTML, and tests share one comparison rule and stay in sync
