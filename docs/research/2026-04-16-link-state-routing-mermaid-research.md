# Link-State Routing Mermaid Export Research - 2026-04-16

## Goal
Make the link-state routing lab more portfolio-friendly by exporting a diagram that can be pasted directly into GitHub-flavored Markdown and documentation.

## Brief findings
- Mermaid `flowchart LR` is widely supported in GitHub Markdown and is good enough for small weighted network diagrams.
- Undirected topology links can be approximated cleanly with bidirectional arrows and inline edge labels.
- A separate overlay for the shortest-path tree helps distinguish the full topology from the chosen forwarding structure.
- Keeping labels short (`SPF <cost>`) avoids clutter while still showing why a tree edge was chosen.

## Scope chosen
- render the normalized topology as a Mermaid flowchart
- optionally highlight the SPF tree rooted at a chosen source router
- keep the output plain text so users can redirect it into docs or artifacts later
