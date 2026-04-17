# 2026-04-17 branch predictor perceptron refresh + self-test

## Refresh points
- A perceptron branch predictor treats branch direction as a binary classification problem over recent global-history bits encoded as `+1` / `-1`.
- Prediction comes from the sign of `bias + Σ(weight_i * history_i)` for the selected perceptron row.
- Training should update the bias and history weights when the prediction is wrong or when the activation magnitude is too small to be considered confident.
- Weight clamping matters in a teaching simulator because it prevents unbounded growth while keeping the predictor state easy to inspect.
- A linearly separable long-history trace is a better perceptron demo than a tiny alternating pattern because it shows why weighted history can generalize beyond short counter tables.

## Self-test cases to encode in unit tests
- `perceptron-majority` generation should be seed-reproducible and produce a single labeled static branch so demos remain deterministic.
- The perceptron predictor should beat gshare and two-bit on the `perceptron-majority` workload with a longer history length.
- `simulate --predictor perceptron --json` should expose threshold, weight limit, and non-zero-weight counts.
- The full `compare` ranking on the perceptron workload should place `perceptron` first for the committed seed/config pair.
- The project docs should include a committed artifact path for the new workload so the slice is easy to resume or demo later.
