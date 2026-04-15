# Distance vector routing diagram export refresh

## Goal
Add presentation-friendly exports so the routing lab is easier to show in a portfolio README, blog post, or interview walkthrough.

## Quick refresh
- Mermaid is convenient for markdown-native portfolio docs and GitHub rendering.
- Graphviz DOT is useful when the user wants richer offline rendering later.
- For this project, a topology snapshot and a final routing-table snapshot are enough to make the simulator more demoable without building a full visualizer.

## Self-test
- Can I explain the difference between a topology diagram and a route snapshot? Yes: topology shows links and weights; route snapshot shows each router's chosen next hop and final cost to destinations.
- Can the same simulation output feed both Mermaid and DOT? Yes, because the simulator already normalizes topology and final routing tables deterministically.
- What is the smallest meaningful CLI extension? A new `export-diagram` subcommand with `--snapshot`, `--format`, and optional `--router` flags.
