# Review pass 1 — chord random start-node sampling

## Focus
Helper/API design and reproducibility contract.

## Checks
- verified `select_benchmark_start_nodes` keeps the old ordered behavior as the default
- verified random mode requires a seed and samples without replacement
- verified synthetic benchmark metadata records both sampling mode and effective seed

## Result
- no code changes needed after this pass
