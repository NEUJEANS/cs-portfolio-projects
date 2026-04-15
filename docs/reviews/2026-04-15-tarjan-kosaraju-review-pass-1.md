# Tarjan vs Kosaraju review pass 1

## Focus
Code-path review of the new `compare` CLI slice.

## Issue found
- `main()` eagerly computed Tarjan SCCs for every subcommand, including `compare`, which already runs both algorithms internally. That added unnecessary duplicate work and muddied the benchmark story.

## Fix applied
- Moved the `compare` branch ahead of the shared Tarjan component computation so timing/reporting stays focused on the requested comparison path.

## Result
- Compare mode no longer pays for an extra unused Tarjan run before printing output.
