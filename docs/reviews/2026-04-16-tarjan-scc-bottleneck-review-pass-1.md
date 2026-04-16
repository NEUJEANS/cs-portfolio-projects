# Tarjan SCC bottleneck review pass 1

- Scope: correctness review of condensation JSON and SCC summary metadata.
- Checks: verified source/bridge/sink/isolated expectations against the sample DAG and targeted tests.
- Issue found: bottleneck-role classification logic was duplicated in both `condensation_dag()` and `summarize_components()`, which risked future drift.
- Fix applied: extracted `_bottleneck_role()` and routed both outputs through the shared helper.
- Result: metadata now stays consistent across JSON and explain views.
