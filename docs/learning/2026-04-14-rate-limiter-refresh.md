# Python Refresh + Self-Test: Rate Limiting

## Refresher
- Use dataclasses to keep limiter state readable.
- Model time as floating-point seconds for deterministic simulation.
- For sliding logs, prune old timestamps before each decision.
- For token buckets, refill based on elapsed time before spending a token.

## Self-test
1. If a fixed window limit is 3 requests per 10 seconds, requests at 0, 1, 2 are allowed and 3 is denied.
2. Sliding log with the same policy allows a request at 10.1 because the request at 0.0 falls out of the window.
3. Token bucket with capacity 2 and refill 1 token/sec allows events at 0 and 0, denies the next at 0, then allows again at 1.

## Implementation choices for this project
- expose all three algorithms behind one CLI
- accept event times as a JSON list or repeated `--event`
- keep the module dependency-free so it is easy to run in interviews
