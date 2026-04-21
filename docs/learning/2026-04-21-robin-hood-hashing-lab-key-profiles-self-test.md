# Self-test note — robin-hood-hashing-lab key profile slice

Date: 2026-04-21

## Refresh
- Rechecked the benchmark pipeline boundaries: raw rows carry trial-level metrics, `summarize_benchmark()` pools them into report slices, and the Markdown/HTML renderers should stay thin consumers of the summary payload.
- Reconfirmed that this project's snapshots and CLI inputs are intentionally string-only, so integer workload coverage had to arrive as a deterministic benchmark generator, not as a second runtime key type.

## Quick self-test
- Added unit coverage for `parse_key_profiles()` alias normalization and invalid-profile rejection.
- Added deterministic generator checks for both `string` and `integer` key profiles plus a disjoint missing-key test for integer workloads.
- Extended report coverage so multi-profile summaries/rendering explicitly include both `Random string IDs` and `Sequential integer IDs` in Markdown and HTML outputs.
- Extended the CLI benchmark flow test so CSV output size and fields reflect both key profiles when `--key-profiles string,integer` is used.
