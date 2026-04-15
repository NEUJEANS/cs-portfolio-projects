# 2026-04-15 mini-mapreduce dataset-family refresh

## Goal
Add multiple synthetic benchmark dataset families without breaking older plugin generators that only accept `(scenario, records, seed)`.

## Quick refresh
- `inspect.signature(callable)` lets the runner detect whether a plugin benchmark hook supports an added `dataset_family` parameter.
- Backward compatibility matters more than perfect type strictness here because existing plugins/tests already rely on the 3-argument form.
- The safest contract is: keep the old form working, allow a 4-argument form, and raise a clear error only when the caller requests a non-default dataset family against an older plugin hook.

## Self-test before coding
- A 3-argument plugin hook should still work for `dataset_family=default`.
- A 4-argument plugin hook should receive `dataset_family` and shape records differently.
- Benchmark JSON/CSV/heatmap/report outputs should all carry the chosen dataset family so artifacts remain self-describing.
