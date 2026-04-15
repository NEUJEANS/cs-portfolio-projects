# Tarjan SCC condensation levels refresh

## Focus
- Tarjan already yields SCCs.
- Once SCCs are collapsed, the condensation graph is a DAG.
- A useful interview-friendly annotation is each component's topological level: the longest distance from any source component.

## Quick self-test
1. Build component DAG edges after SCC assignment.
2. Count incoming edges per component.
3. Start all zero-in-degree components at level 0.
4. Process in topological order and propagate `neighbor_level = max(neighbor_level, current_level + 1)`.
5. Report overall `level_count = max(level) + 1`.

## Why this helps the portfolio piece
- turns SCC output into a stronger dependency-analysis story
- gives recruiters/interviewers a clearer "what would you do with this?" explanation
- stays compact enough for one slice without distorting the original lab
