# 2026-04-15 mini-mapreduce dataset-family discovery refresh

## Goal
Surface plugin-declared dataset-family support automatically without breaking older plugins that only expose a benchmark generator.

## Quick refresh
- Optional module-level metadata is a low-friction way to advertise capabilities without changing the execution signature of the core plugin hooks.
- Validation should happen close to plugin load/use so CLI failures can name the unsupported family and list the supported ones.
- Artifact metadata matters for portfolio work: if a report says a benchmark used `project-week`, it is even better when it also shows the plugin supports `default`, `exam-cram`, and `project-week`.

## Self-test before coding
- A plugin with `BENCHMARK_DATASET_FAMILIES` should render that list in JSON/Markdown/HTML benchmark outputs.
- Requesting an unsupported family should fail with a clear message listing supported families.
- Older plugins without the metadata should continue to work exactly as before.
