# Dependency graph walkthrough — Sample Graph

- Source manifest: `projects/dependency-graph-planner/sample_graph.json`
- Task count: `5`
- Parallel layers: `4`
- Estimated makespan: `8`
- Critical path: `lint -> compile -> unit -> publish`

## Linked artifacts

- [GitHub-friendly Mermaid preview](sample_graph_mermaid.md)
- [Mermaid source](sample_graph.mmd)
- [Graphviz DOT source](sample_graph.dot)

## Portfolio summary

- deterministic ready-queue ordering keeps the plan stable: `lint, compile, package, unit, publish`
- widest parallel layer: `layer 2` with `2` task(s): `package`, `unit`
- non-critical slack budget available for schedule tradeoffs: `1` time units

## Parallel layer windows

- Layer 0 (`0` → `1`): `lint`
- Layer 1 (`1` → `5`): `compile`
- Layer 2 (`5` → `7`): `package`, `unit`
- Layer 3 (`7` → `8`): `publish`

## Task timing table

| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| lint | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | ruff check . |
| compile | 1 | lint | 4 | — | 1 | 5 | 1 | 5 | 0 | yes | python -m build |
| package | 2 | compile | 1 | — | 5 | 6 | 6 | 7 | 1 | no | python -m zipapp |
| unit | 2 | compile | 2 | — | 5 | 7 | 5 | 7 | 0 | yes | pytest |
| publish | 3 | unit, package | 1 | — | 7 | 8 | 7 | 8 | 0 | yes | twine upload dist/* |

## Deterministic execution order

1. `lint`
   - Dependencies: `ready at start`
   - Window: `0 → 1`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `ruff check .`
2. `compile`
   - Dependencies: `lint`
   - Window: `1 → 5`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `python -m build`
3. `package`
   - Dependencies: `compile`
   - Window: `5 → 6`
   - Slack: `1`
   - Resources: `generic worker`
   - Command: `python -m zipapp`
4. `unit`
   - Dependencies: `compile`
   - Window: `5 → 7`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `pytest`
5. `publish`
   - Dependencies: `unit`, `package`
   - Window: `7 → 8`
   - Slack: `0`
   - Resources: `generic worker`
   - Command: `twine upload dist/*`
