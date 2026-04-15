# mini-mapreduce typed plugin outputs research

Date: 2026-04-15

## Goal
Make plugin jobs more portfolio-worthy by supporting reducer outputs that are still JSON-safe but not limited to integers.

## Findings
- Real MapReduce-style pipelines often emit intermediate structured values such as partial sums and counts, then reduce them into averages, ratios, or small summary objects.
- For a lightweight CLI portfolio project, the safest expansion is JSON-serializable outputs only: strings, numbers, booleans, null, arrays, and objects.
- Once reducer outputs are not guaranteed to be numeric, output ordering should stop assuming descending numeric sort for every job.
- Reducer-bucket stats should measure merge workload, not depend on arithmetic over final reducer outputs.

## Decision
- Allow plugin mappers, combiners, and reducers to exchange JSON-serializable values.
- Keep built-in jobs unchanged.
- Preserve descending value sort for purely numeric outputs; otherwise fall back to deterministic key ordering.
- Count reducer bucket `records` as merged partial values per key bucket so stats remain meaningful for non-numeric reducers.
