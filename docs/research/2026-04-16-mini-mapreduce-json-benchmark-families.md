# Mini MapReduce JSON benchmark families research

Date: 2026-04-16 08:20 UTC
Project: `mini-mapreduce-lab`

## Goal
Pick benchmark shapes that make the built-in `json-group-count` job feel like a realistic systems/data-engineering portfolio demo instead of a toy counter.

## Notes
- Event-stream demos are stronger when the grouped field maps to recognizable operational states such as `status`, incident lifecycle steps, or deployment outcomes.
- Balanced fixtures should keep a small fixed label set so reducer-balance comparisons are easy to explain.
- Skewed fixtures should concentrate most records in one or two hot labels because that mirrors real production hot-key behavior and makes reducer skew visible in artifacts.
- Extra fields like `service`, `team`, or `region` make the JSONL inputs look authentic without changing the grouped-key contract.

## Chosen families
- `default`: generic ingestion/event statuses (`ok`, `retry`, `error`, `queued`)
- `incidents`: incident lifecycle states (`detected`, `triaged`, `mitigated`, `resolved`)
- `deployments`: release pipeline states (`queued`, `running`, `passed`, `rolled_back`)
