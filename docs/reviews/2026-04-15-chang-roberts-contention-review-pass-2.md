# chang-roberts contention benchmark review — pass 2 (2026-04-15)

## Focus
Output sanity and presentation value.

## Checks
- Ran the benchmark CLI on the sample ring `8 3 12 6`.
- Inspected JSON rows for monotonic cost trends as initiator count increases.
- Exported JSON and CSV artifacts to ensure the slice is usable in README screenshots, charts, and portfolio write-ups.

## Findings
- Average total message cost increases from 1 initiator to 4 initiators as expected.
- Average rounds decrease slightly while delivery count rises, which is a good discussion point about lockstep contention.
- Artifact formats are concise and presentation-friendly.

## Fix applied
- Persisted benchmark outputs under `artifacts/` so the slice is demonstrable without rerunning commands during review.
