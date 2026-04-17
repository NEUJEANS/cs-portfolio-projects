# Network-flow proof-card SVG review - pass 2

## Focus
CLI behavior and artifact generation for the new `--svg-out` flow.

## Checks run
- `python3 -m py_compile projects/network-flow-lab/network_flow.py`
- `python3 -m unittest tests.test_network_flow_lab`
- `python3 projects/network-flow-lab/network_flow.py demo --algorithm dinic --markdown-out docs/artifacts/network-flow-lab/sample-flow-proof.md --svg-out docs/artifacts/network-flow-lab/sample-flow-proof.svg`
- `python3 projects/network-flow-lab/network_flow.py match-demo --algorithm dinic --markdown-out docs/artifacts/network-flow-lab/sample-matching-proof.md --svg-out docs/artifacts/network-flow-lab/sample-matching-proof.svg`

## Findings
- The new CLI path emits both Markdown and SVG proof artifacts successfully for flow and matching demos.
- The refreshed proof artifacts line up with README examples and give the project screenshot-ready committed outputs.

## Fix applied
- No additional code change was needed after this pass.

## Result
- The proof-card export path works end to end from CLI flag to committed artifact.
