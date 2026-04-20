# 2026-04-20 learning refresh — graph-routing gallery

## Brief refresh takeaway
- A gallery export is strongest when the manifest stays declarative: scenario metadata plus already-generated artifact links, with the landing page recomputing only lightweight comparison summaries.
- Multi-scenario portfolio pages need story diversity more than raw volume. One same-cost reroute, one negative-cycle incident, and one reachability regression tell a much better interview story than three nearly identical weight tweaks.
- Relative links matter for static artifact bundles because they let the Markdown and HTML outputs stay portable inside the repo and on simple static hosts.

## Self-test
1. Why use a manifest instead of hard-coding scenarios inside the exporter?
   - So the gallery stays data-driven, easy to extend, and reusable for different artifact bundles without code edits.
2. Why include both Markdown and HTML gallery outputs?
   - Markdown is easy to review in-repo and GitHub, while HTML gives a richer static landing page for screenshot-friendly portfolio hosting.
3. Why keep the scenario cards self-contained?
   - So each routing story can be scanned independently and linked directly in a portfolio or review thread.
4. Why add a link-failure fixture instead of only reusing the existing same-cost reroute case?
   - Because a gallery should show different routing failure modes, and the reachability regression adds a clearer outage-style story.
