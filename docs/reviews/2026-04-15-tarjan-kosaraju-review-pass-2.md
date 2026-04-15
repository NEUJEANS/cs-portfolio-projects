# Tarjan vs Kosaraju review pass 2

## Focus
CLI/documentation consistency review.

## Issue found
- The parser description still said the tool analyzed SCCs with Tarjan's algorithm only, even though the project now exposes both Tarjan and Kosaraju workflows.

## Fix applied
- Updated the CLI description to mention both Tarjan and Kosaraju workflows.

## Result
- Help text now matches the actual project scope and avoids underselling the new slice.
