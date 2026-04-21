# Research note — robin-hood-hashing-lab key profile slice

Date: 2026-04-21

## What I checked
- Tried a brief grounded web search for Robin Hood hashing benchmark guidance on integer vs string key workloads, but `web_search` returned `Gemini API error (503)` twice because the search model was unavailable.
- Rechecked the repo's current Robin Hood benchmark/report architecture instead: the table implementation and snapshot format are string-keyed, while the benchmark pipeline already supports deterministic workload families, CSV/JSON exports, and report aggregation across slices.

## Decision
- Keep the table and snapshot contract string-keyed.
- Add benchmark-level `key_profile` support instead of introducing a second table implementation or mixed runtime key types.
- Model the integer workload as canonical decimal-string IDs generated from shuffled sequential numbers. That gives a meaningfully different identifier shape while preserving the existing CLI, snapshot validator, and JSON artifact format.

## Why this slice is still useful without broader key types
- It expands the benchmark story from one identifier shape to two, which makes the portfolio artifact less toy-like during interviews.
- It keeps the benchmark deterministic, because both the string and integer profiles are generated from stable seed material.
- It avoids widening the project scope into a typed-hash-table rewrite when the documented follow-up was really about workload shape coverage.
