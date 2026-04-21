# Deadlock detector visual export slice research

## Goal
Add lightweight, dependency-free SVG and HTML exports for the deadlock detector so the wait-for and allocation demos are easier to show in a portfolio without installing Graphviz or opening raw JSON.

## Brief notes
- A wait-for graph wants a simple process-only node layout with the deadlock cycle highlighted, because the core story is who is waiting on whom and where the cycle closes.
- A resource-allocation snapshot is easier to read as a bipartite process/resource diagram: held edges from resources to processes, request edges from processes to resources, and shortage labels for blocked requests.
- Static SVG is a good fit for this slice because it stays deterministic, commits cleanly into the repo, and can be embedded directly into Markdown, slides, or HTML wrap-ups.
- HTML should stay self-contained and boring: summary metrics, one embedded SVG, and small tables for the details already present in JSON.

## Sources
- Prior deadlock-detector wrap-up from 2026-04-21, which explicitly called out wait-for and resource-allocation visuals as the next missing storytelling layer.
- Existing project JSON output shape, which already contains the cycle, finish order, blocked processes, and blocking shortages needed to drive static diagrams without extra dependencies.
