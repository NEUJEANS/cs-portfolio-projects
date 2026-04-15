# Review Pass 3 - Distributed Snapshot Lab

## Focus
- defensive validation
- output cleanliness
- resumability

## Findings
1. Marker-delay overrides could reference unknown channels without an early validation error.
2. Empty channel-state entries were noisy and added no value to the JSON output.

## Fixes applied
- validated `sender->receiver` marker-delay channels against the current process set
- rejected self-channel marker delays
- omitted empty channel-state arrays from the snapshot output
- reran project tests plus repository regression tests
