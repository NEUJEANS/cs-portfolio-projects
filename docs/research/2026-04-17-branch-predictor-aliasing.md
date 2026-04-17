# 2026-04-17 branch predictor aliasing notes

## Goal
Make `branch-predictor-lab` better at explaining predictor-table interference, not just raw predictor ranking.

## Refresher takeaways
- Small bimodal/local tables usually index with low-order PC bits, so different static branches can fight over the same counter entry.
- When colliding branches have opposite taken biases, the shared counter gets trained in both directions and accuracy drops even if each branch is individually predictable.
- Increasing table size can separate those PCs without changing the predictor logic, which makes aliasing a nice interview-friendly demo of capacity/interference trade-offs.
- Gshare changes the effective index with history, but the simplest, most teachable first step is still a static PC-index collision summary because it matches the one-bit/two-bit/local chooser tables students already know.

## Implementation choice for this slice
- Add an `alias-thrash` synthetic workload with two intentional collision buckets at table size 16.
- Add compare-output alias summaries so the CLI and artifact cards can point at exact colliding indices and per-PC taken rates.
- Keep the scope static and explainable now; leave dynamic gshare-index collision analysis for a future slice.
